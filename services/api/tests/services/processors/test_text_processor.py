from pathlib import Path

import pytest

from app.services.processors.text_processor import TextProcessor


def test_text_processor_supports_txt():
    """Test TXT and MD support"""
    processor = TextProcessor()
    assert processor.supports_file_type("txt") is True
    assert processor.supports_file_type("md") is True
    assert processor.supports_file_type("pdf") is False


def test_process_simple_text(tmp_path):
    """Test processing simple text file"""
    text_file = tmp_path / "test.txt"
    text_file.write_text("Paragraph one.\n\nParagraph two.")

    processor = TextProcessor()
    result = processor.process(text_file)

    assert result.document_type == "txt"
    assert len(result.elements) >= 2


def test_process_markdown_with_headings(tmp_path):
    """Test markdown heading parsing with regex"""
    md_file = tmp_path / "test.md"
    md_content = """# Main Title

This is the introduction paragraph.

## Section 1

Content under section 1.

### Subsection 1.1

Detailed content here.

## Section 2

More content in section 2."""

    md_file.write_text(md_content)

    processor = TextProcessor()
    result = processor.process(md_file)

    assert result.document_type == "md"

    # Check that headings are detected
    headings = [e for e in result.elements if e.element_type == "heading"]
    assert len(headings) == 4  # Main Title, Section 1, Subsection 1.1, Section 2

    # Check heading levels
    assert headings[0].section_level == 1
    assert headings[1].section_level == 2
    assert headings[2].section_level == 3
    assert headings[3].section_level == 2

    # Check section hierarchy
    assert headings[0].section_title == "Main Title"
    assert headings[1].section_title == "Main Title > Section 1"
    assert headings[2].section_title == "Main Title > Section 1 > Subsection 1.1"
    assert headings[3].section_title == "Main Title > Section 2"

    # Check paragraphs have section context
    paragraphs = [e for e in result.elements if e.element_type == "paragraph"]
    assert len(paragraphs) > 0
    assert any(p.section_title is not None for p in paragraphs)
