"""Document processing service coordinating processors and chunking."""
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from app.models.schemas import DocumentType
from app.services.processors.base_processor import BaseDocumentProcessor, ProcessedDocument
from app.services.processors.pdf_processor import PDFProcessor
from app.services.processors.docx_processor import DOCXProcessor
from app.services.processors.text_processor import TextProcessor
from app.services.processors.csv_processor import CSVProcessor
from app.services.chunking.semantic_chunker import SemanticChunker
from app.services.chunking.semantic_chunker_v2 import SemanticChunkerV2
from app.core.config import settings
from app.utils.token_counter import TokenCounter


class SemanticChunkerV2Wrapper:
    """
    Wrapper for SemanticChunkerV2 to match the interface of legacy SemanticChunker.

    This wrapper provides synchronous methods that internally run async operations,
    allowing seamless integration with existing code while using the new semantic chunker.
    """

    def __init__(
        self,
        min_chunk_size: int = 128,
        max_chunk_size: int = 512,
        breakpoint_percentile: float = 95.0
    ):
        """Initialize the wrapper with a SemanticChunkerV2 instance."""
        self.chunker = SemanticChunkerV2(
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
            breakpoint_percentile=breakpoint_percentile
        )
        self.token_counter = TokenCounter()

    def chunk_with_metadata(
        self,
        text: str,
        section_context: str = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text and return with metadata (synchronous wrapper for async method).

        Args:
            text: Text to chunk
            section_context: Optional section context (not used in v2 but kept for compatibility)

        Returns:
            List of dicts with 'content' and 'tokens' keys
        """
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        chunks = loop.run_until_complete(self.chunker.chunk_text(text))

        # Convert to expected format
        result = []
        for chunk in chunks:
            result.append({
                'content': chunk.text,
                'tokens': chunk.token_count or len(chunk.text.split())
            })

        return result


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

        # Select chunking strategy based on configuration
        if settings.CHUNKING_STRATEGY == "semantic":
            # Use new semantic chunker with percentile-based breakpoints
            self.chunker = SemanticChunkerV2Wrapper(
                min_chunk_size=settings.SEMANTIC_MIN_CHUNK_SIZE,
                max_chunk_size=settings.SEMANTIC_MAX_CHUNK_SIZE,
                breakpoint_percentile=settings.SEMANTIC_BREAKPOINT_PERCENTILE
            )
        else:
            # Use legacy recursive chunker
            self.chunker = SemanticChunker(
                chunk_size=settings.CHUNK_SIZE,
                overlap=settings.CHUNK_OVERLAP
            )

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

    def process_and_chunk(
        self,
        file_path: Path,
        document_type: DocumentType
    ) -> List[Dict]:
        """
        Process document and create chunks with metadata.

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
                    section_chunks = self.chunker.chunk_with_metadata(
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
            section_chunks = self.chunker.chunk_with_metadata(
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
