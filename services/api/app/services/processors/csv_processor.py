"""CSV document processor."""
from pathlib import Path
from typing import List
import csv
from app.services.processors.base_processor import (
    BaseDocumentProcessor,
    DocumentElement,
    ProcessedDocument
)


class CSVProcessor(BaseDocumentProcessor):
    """Processor for CSV files - converts rows to natural language."""

    def supports_file_type(self, file_type: str) -> bool:
        """Check if this processor supports the file type."""
        return file_type.lower() == "csv"

    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process CSV and convert rows to searchable text.
        Each row becomes an element with headers prepended.

        Args:
            file_path: Path to CSV file

        Returns:
            ProcessedDocument with row elements
        """
        elements: List[DocumentElement] = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            for row_idx, row in enumerate(reader):
                # Convert row to natural language
                row_text = "In CSV data: " + ", ".join(
                    f"{key}={value}" for key, value in row.items() if value
                )

                element = DocumentElement(
                    content=row_text,
                    element_type='csv_row',
                    metadata={
                        'row_index': row_idx,
                        'headers': list(headers) if headers else [],
                        'values': dict(row)
                    }
                )
                elements.append(element)

        metadata = {
            'num_rows': len(elements),
            'headers': list(headers) if headers else []
        }

        return ProcessedDocument(
            elements=elements,
            metadata=metadata,
            document_type='csv'
        )
