from pathlib import Path

import pytest

from app.services.processors.csv_processor import CSVProcessor


def test_csv_processor_supports_csv():
    """Test CSV support"""
    processor = CSVProcessor()
    assert processor.supports_file_type("csv") is True


def test_process_csv(tmp_path):
    """Test processing CSV file"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name,Age,City\nAlice,30,NYC\nBob,25,LA")

    processor = CSVProcessor()
    result = processor.process(csv_file)

    assert result.document_type == "csv"
    assert len(result.elements) >= 2  # At least 2 data rows
