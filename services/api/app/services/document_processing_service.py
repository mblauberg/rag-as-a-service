"""Document processing service coordinating processors and chunking."""
from pathlib import Path
from typing import Dict, List
from app.models.schemas import DocumentType
from app.services.processors.base_processor import BaseDocumentProcessor, ProcessedDocument
from app.services.processors.pdf_processor import PDFProcessor
from app.services.processors.docx_processor import DOCXProcessor
from app.services.processors.text_processor import TextProcessor
from app.services.processors.csv_processor import CSVProcessor
from app.services.chunking.semantic_chunker import SemanticChunker


class DocumentProcessingService:
    """
    Service for processing documents with appropriate processors.
    Coordinates document parsing, chunking, and metadata extraction.
    """

    def __init__(self):
        """Initialize with all available processors."""
        self.processors: Dict[DocumentType, BaseDocumentProcessor] = {
            DocumentType.PDF: PDFProcessor(),
            DocumentType.DOCX: DOCXProcessor(),
            DocumentType.TXT: TextProcessor(),
            DocumentType.MD: TextProcessor(),
            DocumentType.CSV: CSVProcessor(),
        }

        self.chunker = SemanticChunker(
            chunk_size=400,
            overlap=80
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
                            'metadata': element.metadata
                        })

                    current_section = []

                # Start new section
                current_section_title = element.section_title
                current_section_level = element.section_level or 0

            else:
                # Add to current section
                current_section.append(element.content)
                if element.page_number:
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
