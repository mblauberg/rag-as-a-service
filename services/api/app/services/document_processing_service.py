"""Document processing service coordinating processors and chunking."""
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.chunking.semantic_chunker import SemanticChunker
from app.services.processors.base_processor import BaseDocumentProcessor
from app.services.processors.csv_processor import CSVProcessor
from app.services.processors.docx_processor import DOCXProcessor
from app.services.processors.pdf_processor import PDFProcessor
from app.services.processors.text_processor import TextProcessor
from app.utils.file_type_detector import DocumentType


class DocumentProcessingService:
    """
    Service for processing documents with appropriate processors.
    Coordinates document parsing, chunking, and metadata extraction.
    """

    def __init__(self) -> None:
        """Initialize with all available processors and appropriate chunker based on config."""
        self.processors: dict[DocumentType, BaseDocumentProcessor] = {
            DocumentType.PDF: PDFProcessor(),
            DocumentType.DOCX: DOCXProcessor(),
            DocumentType.TXT: TextProcessor(),
            DocumentType.MD: TextProcessor(),
            DocumentType.CSV: CSVProcessor(),
        }

        # Use semantic chunker with embedding-based breakpoint detection
        # Removed legacy fallback - SemanticChunker is the canonical implementation
        self.chunker = SemanticChunker(
            min_chunk_size=settings.chunking.min_chunk_size,
            max_chunk_size=settings.chunking.max_chunk_size,
            breakpoint_percentile=settings.chunking.breakpoint_percentile,
        )

    def get_processor(self, document_type: DocumentType) -> BaseDocumentProcessor:
        """Get appropriate processor for document type.

        Selects specialized processor based on file format:
        - PDF: PyMuPDF-based extraction with layout preservation
        - DOCX: python-docx for structured document parsing
        - TXT/MD: Plain text processor with encoding detection
        - CSV: Pandas-based tabular data processor

        Args:
            document_type: Type of document (from file extension detection).
                Must be one of: PDF, DOCX, TXT, MD, CSV.

        Returns:
            Document processor instance configured for the file type.
            Each processor implements BaseDocumentProcessor interface with
            process() method returning structured elements.

        Raises:
            ValueError: If document_type is not in supported formats.
                Supported types are defined in self.processors registry.
        """
        if document_type not in self.processors:
            raise ValueError(f"Unsupported document type: {document_type}")

        return self.processors[document_type]

    async def process_and_chunk(
        self, file_path: Path, document_type: DocumentType
    ) -> list[dict[str, object]]:
        """Process document and create semantic chunks with metadata.

        Implements a two-phase document processing pipeline:

        Phase 1 - Document Parsing:
        - Selects appropriate processor for file type (PDF, DOCX, TXT, etc.)
        - Extracts structured elements (headings, paragraphs, tables)
        - Preserves document hierarchy and metadata (sections, pages)

        Phase 2 - Semantic Chunking:
        - Groups elements by section for contextual coherence
        - Applies SemanticChunker with embedding-based breakpoint detection
        - Creates chunks respecting semantic boundaries (not arbitrary splits)
        - Attaches rich metadata: section titles, page numbers, hierarchy

        The SemanticChunker uses sentence embeddings to detect topic shifts,
        ensuring chunks represent coherent semantic units rather than arbitrary
        text windows. This improves retrieval quality by keeping related
        content together.

        This method is async to support embedding-based chunking operations.

        Args:
            file_path: Path to uploaded document file on disk.
            document_type: Type of document (PDF, DOCX, TXT, MD, CSV).
                Determines which processor to use for parsing.

        Returns:
            List of chunk dictionaries, each containing:
            - content (str): Chunk text content
            - tokens (int): Approximate token count
            - section_title (str | None): Parent section heading
            - section_level (int): Heading hierarchy level (0=top)
            - page_number (int | None): Page number where chunk appears
            - metadata (dict): Additional processor-specific metadata

        Note:
            Chunks are created per section to maintain semantic coherence.
            A long section may produce multiple chunks, while short sections
            may be combined if they fit within max_chunk_size.

        Example:
            >>> service = DocumentProcessingService()
            >>> chunks = await service.process_and_chunk(
            ...     Path("/tmp/paper.pdf"),
            ...     DocumentType.PDF
            ... )
            >>> print(f"Created {len(chunks)} chunks")
            >>> print(f"First chunk: {chunks[0]['content'][:100]}")
        """
        # Get processor and process document
        processor = self.get_processor(document_type)
        processed_doc = processor.process(file_path)

        # Group elements by section for better chunking
        chunks = []
        current_section: list[str] = []
        current_section_title: str | None = None
        current_section_level = 0
        current_page = None

        for element in processed_doc.elements:
            # Update section tracking
            if element.element_type == "heading":
                # Flush previous section
                if current_section:
                    section_text = "\n\n".join(current_section)
                    section_chunks = await self._chunk_text(
                        section_text, section_context=current_section_title
                    )

                    for chunk in section_chunks:
                        chunks.append(
                            {
                                "content": chunk["content"],
                                "tokens": chunk["tokens"],
                                "section_title": current_section_title,
                                "section_level": current_section_level,
                                "page_number": current_page,
                                "metadata": {},
                            }
                        )

                    current_section = []

                # Start new section
                current_section_title = element.section_title
                current_section_level = element.section_level or 0

            else:
                # Add to current section
                current_section.append(element.content)
                if element.page_number is not None:
                    current_page = element.page_number

        # Flush final section
        if current_section:
            section_text = "\n\n".join(current_section)
            section_chunks = await self._chunk_text(
                section_text, section_context=current_section_title
            )

            for chunk in section_chunks:
                chunks.append(
                    {
                        "content": chunk["content"],
                        "tokens": chunk["tokens"],
                        "section_title": current_section_title,
                        "section_level": current_section_level,
                        "page_number": current_page,
                        "metadata": {},
                    }
                )

        return chunks

    async def _chunk_text(
        self, text: str, section_context: str | None = None
    ) -> list[dict[str, Any]]:
        """Chunk text using semantic breakpoint detection.

        Applies SemanticChunker which uses sentence embeddings to detect
        topic boundaries. This creates semantically coherent chunks rather
        than arbitrary fixed-size windows.

        Algorithm overview:
        1. Split text into sentences
        2. Embed each sentence using sentence-transformers
        3. Compute cosine distances between adjacent sentence embeddings
        4. Detect breakpoints at high-distance boundaries (topic shifts)
        5. Create chunks between breakpoints, respecting min/max size

        This approach preserves semantic coherence, ensuring each chunk
        covers a single topic or concept. Particularly effective for
        technical documents with clear topic transitions.

        Args:
            text: Text to chunk (typically a document section).
            section_context: Optional section heading for context.
                Currently unused but reserved for future hierarchical chunking.

        Returns:
            List of dictionaries, each containing:
            - content (str): Chunk text
            - tokens (int): Approximate token count (word-based estimate)

        Note:
            Token count is estimated from word count. For precise token
            counting, use a tokenizer like tiktoken (GPT) or transformers.
        """
        # Use async SemanticChunker
        chunk_results = await self.chunker.chunk_text(text)

        # Convert ChunkResult objects to expected format
        return [
            {
                "content": chunk.text,
                "tokens": chunk.token_count or len(chunk.text.split()),
            }
            for chunk in chunk_results
        ]
