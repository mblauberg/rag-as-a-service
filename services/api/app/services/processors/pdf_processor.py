"""PDF document processor."""
from pathlib import Path
from typing import List
import pypdf
from app.services.processors.base_processor import (
    BaseDocumentProcessor,
    DocumentElement,
    ProcessedDocument
)


class PDFProcessor(BaseDocumentProcessor):
    """Processor for PDF documents."""

    def supports_file_type(self, file_type: str) -> bool:
        """Check if this processor supports the file type."""
        return file_type.lower() == "pdf"

    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process PDF and extract text with page numbers.

        Args:
            file_path: Path to PDF file

        Returns:
            ProcessedDocument with elements
        """
        elements: List[DocumentElement] = []

        with open(file_path, 'rb') as f:
            pdf_reader = pypdf.PdfReader(f)

            metadata = {
                'num_pages': len(pdf_reader.pages),
                'title': pdf_reader.metadata.title if pdf_reader.metadata else None,
                'author': pdf_reader.metadata.author if pdf_reader.metadata else None,
            }

            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()

                if text.strip():
                    # Split into paragraphs
                    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

                    for para in paragraphs:
                        element = DocumentElement(
                            content=para,
                            element_type='paragraph',
                            metadata={'source': 'pdf'},
                            page_number=page_num,
                        )
                        elements.append(element)

        return ProcessedDocument(
            elements=elements,
            metadata=metadata,
            document_type='pdf'
        )
