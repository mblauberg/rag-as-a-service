"""Text and Markdown document processor."""
from pathlib import Path
from typing import List
import re
from app.services.processors.base_processor import (
    BaseDocumentProcessor,
    DocumentElement,
    ProcessedDocument
)


class TextProcessor(BaseDocumentProcessor):
    """Processor for plain text and Markdown files."""

    def supports_file_type(self, file_type: str) -> bool:
        """Check if this processor supports the file type."""
        return file_type.lower() in ["txt", "md", "markdown"]

    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process text/markdown file and extract structure.

        Args:
            file_path: Path to text file

        Returns:
            ProcessedDocument with elements
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        file_type = file_path.suffix.lstrip('.').lower()
        if file_type == 'markdown':
            file_type = 'md'

        elements: List[DocumentElement] = []

        if file_type == 'md':
            # Parse markdown structure
            elements = self._parse_markdown(content)
        else:
            # Plain text - split by paragraphs
            elements = self._parse_plaintext(content)

        metadata = {
            'char_count': len(content),
            'line_count': content.count('\n') + 1
        }

        return ProcessedDocument(
            elements=elements,
            metadata=metadata,
            document_type=file_type
        )

    def _parse_markdown(self, content: str) -> List[DocumentElement]:
        """Parse markdown with heading structure."""
        elements = []
        lines = content.split('\n')
        current_section = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for ATX-style headings (# Heading)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # Update section hierarchy
                current_section = current_section[:level-1] + [title]

                element = DocumentElement(
                    content=title,
                    element_type='heading',
                    metadata={'heading_level': level},
                    section_level=level,
                    section_title=' > '.join(current_section)
                )
                elements.append(element)

            elif line.strip():
                # Regular content - collect consecutive non-empty lines
                para_lines = [line]
                i += 1
                while i < len(lines) and lines[i].strip() and not re.match(r'^#{1,6}\s+', lines[i]):
                    para_lines.append(lines[i])
                    i += 1
                i -= 1  # Back up one

                element = DocumentElement(
                    content='\n'.join(para_lines),
                    element_type='paragraph',
                    metadata={},
                    section_title=' > '.join(current_section) if current_section else None
                )
                elements.append(element)

            i += 1

        return elements

    def _parse_plaintext(self, content: str) -> List[DocumentElement]:
        """Parse plain text by paragraphs."""
        elements = []
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        for para in paragraphs:
            element = DocumentElement(
                content=para,
                element_type='paragraph',
                metadata={}
            )
            elements.append(element)

        return elements
