"""Document processing service coordinating processors and chunking."""
from pathlib import Path
from typing import Dict, List, Any, Union
from app.models.schemas import DocumentType
from app.services.processors.base_processor import BaseDocumentProcessor, ProcessedDocument
from app.services.processors.pdf_processor import PDFProcessor
from app.services.processors.docx_processor import DOCXProcessor
from app.services.processors.text_processor import TextProcessor
from app.services.processors.csv_processor import CSVProcessor
from app.services.chunking.semantic_chunker_v2 import SemanticChunkerV2, ChunkResult
from app.core.config import settings


class DocumentProcessingService:
    """
    Service for processing documents with appropriate processors.
    Coordinates document parsing, chunking, and metadata extraction.
    """

    def __init__(self):
        """Initialize with all available processors and appropriate chunker based on config."""
        self.processors: Dict[DocumentType, BaseDocumentProcessor] = {
            DocumentType.PDF: PDFProcessor(),
            DocumentType.DOCX: DOCXProcessor(),
            DocumentType.TXT: TextProcessor(),
            DocumentType.MD: TextProcessor(),
            DocumentType.CSV: CSVProcessor(),
        }

        # Use semantic chunker with embedding-based breakpoint detection
        # Removed legacy fallback - SemanticChunkerV2 is the canonical implementation
        self.chunker = SemanticChunkerV2(
            min_chunk_size=settings.chunking.min_chunk_size,
            max_chunk_size=settings.chunking.max_chunk_size,
            breakpoint_percentile=settings.chunking.breakpoint_percentile
        )
        self.use_async_chunker = True

    def get_processor(self, document_type: DocumentType) -> BaseDocumentProcessor:
        """
        Get appropriate processor for document type.

        Args:
            document_type: Type of document

        Returns:
            Document processor instance

        Raises:
            ValueError: If document type not supported
        """
        if document_type not in self.processors:
            raise ValueError(f"Unsupported document type: {document_type}")

        return self.processors[document_type]

    async def process_and_chunk(
        self,
        file_path: Path,
        document_type: DocumentType
    ) -> List[Dict]:
        """
        Process document and create chunks with metadata.

        This method is now async to support both synchronous and asynchronous chunkers.
        The SemanticChunkerV2 uses async operations for embedding-based chunking.

        Args:
            file_path: Path to document
            document_type: Type of document

        Returns:
            List of chunk dicts with content, metadata, tokens
        """
        # Get processor and process document
        processor = self.get_processor(document_type)
        processed_doc = processor.process(file_path)

        # Group elements by section for better chunking
        chunks = []
        current_section = []
        current_section_title = None
        current_section_level = 0
        current_page = None

        for element in processed_doc.elements:
            # Update section tracking
            if element.element_type == 'heading':
                # Flush previous section
                if current_section:
                    section_text = '\n\n'.join(current_section)
                    section_chunks = await self._chunk_text(
                        section_text,
                        section_context=current_section_title
                    )

                    for chunk in section_chunks:
                        chunks.append({
                            'content': chunk['content'],
                            'tokens': chunk['tokens'],
                            'section_title': current_section_title,
                            'section_level': current_section_level,
                            'page_number': current_page,
                            'metadata': {}
                        })

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
            section_text = '\n\n'.join(current_section)
            section_chunks = await self._chunk_text(
                section_text,
                section_context=current_section_title
            )

            for chunk in section_chunks:
                chunks.append({
                    'content': chunk['content'],
                    'tokens': chunk['tokens'],
                    'section_title': current_section_title,
                    'section_level': current_section_level,
                    'page_number': current_page,
                    'metadata': {}
                })

        return chunks

    async def _chunk_text(
        self,
        text: str,
        section_context: str = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text using the configured chunker (handles both sync and async chunkers).

        Args:
            text: Text to chunk
            section_context: Optional section context

        Returns:
            List of dicts with 'content' and 'tokens' keys
        """
        if self.use_async_chunker:
            # Use async SemanticChunkerV2
            chunk_results = await self.chunker.chunk_text(text)

            # Convert ChunkResult objects to expected format
            return [
                {
                    'content': chunk.text,
                    'tokens': chunk.token_count or len(chunk.text.split())
                }
                for chunk in chunk_results
            ]
        else:
            # Use legacy synchronous chunker
            return self.chunker.chunk_with_metadata(text, section_context)
