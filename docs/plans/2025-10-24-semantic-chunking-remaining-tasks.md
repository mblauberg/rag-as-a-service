# Semantic Chunking Remaining Tasks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Complete the semantic chunking and multi-format document processing implementation by building processors, integrating with existing upload/search endpoints, and updating the frontend.

**Architecture:** Build modular document processors (PDF, DOCX, TXT/MD, CSV, XLSX, PPTX, HTML) that extract structured content, use SemanticChunker to create 400-token chunks with 80-token overlap, store rich metadata in PostgreSQL, and update API endpoints to use the new processing pipeline.

**Tech Stack:** pypdf, python-docx, langchain-text-splitters, tiktoken, openpyxl, python-pptx, beautifulsoup4, FastAPI, SQLAlchemy, PostgreSQL

**Progress:** Tasks 1-5 completed (database migration, models, schemas, dependencies, token counter). Starting from Task 6.

---

## Phase 2: File Processing Infrastructure (Continued)

### Task 6: Create File Type Detector

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/utils/file_type_detector.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/utils/test_file_type_detector.py`

**Step 1: Write failing test**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/utils/test_file_type_detector.py`:

```python
import pytest
from app.utils.file_type_detector import FileTypeDetector
from app.models.schemas import DocumentType


def test_detect_pdf():
    """Test PDF detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("document.pdf") == DocumentType.PDF


def test_detect_docx():
    """Test DOCX detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("report.docx") == DocumentType.DOCX


def test_detect_txt():
    """Test TXT detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("notes.txt") == DocumentType.TXT


def test_detect_markdown():
    """Test Markdown detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("README.md") == DocumentType.MD


def test_detect_csv():
    """Test CSV detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("data.csv") == DocumentType.CSV


def test_detect_unsupported():
    """Test unsupported file type"""
    detector = FileTypeDetector()
    with pytest.raises(ValueError, match="Unsupported file type"):
        detector.detect_from_filename("image.jpg")


def test_is_supported_true():
    """Test is_supported returns True for supported types"""
    detector = FileTypeDetector()
    assert detector.is_supported("document.pdf") is True


def test_is_supported_false():
    """Test is_supported returns False for unsupported types"""
    detector = FileTypeDetector()
    assert detector.is_supported("image.jpg") is False
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/utils/test_file_type_detector.py -v`
Expected: FAIL - "No module named 'app.utils.file_type_detector'"

**Step 3: Implement file type detector**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/utils/file_type_detector.py`:

```python
"""File type detection utility."""
from pathlib import Path
from app.models.schemas import DocumentType


class FileTypeDetector:
    """Detect document type from filename or content."""

    EXTENSION_MAP = {
        '.pdf': DocumentType.PDF,
        '.docx': DocumentType.DOCX,
        '.txt': DocumentType.TXT,
        '.md': DocumentType.MD,
        '.markdown': DocumentType.MD,
        '.csv': DocumentType.CSV,
        '.xlsx': DocumentType.XLSX,
        '.xls': DocumentType.XLSX,
        '.pptx': DocumentType.PPTX,
        '.ppt': DocumentType.PPTX,
        '.html': DocumentType.HTML,
        '.htm': DocumentType.HTML,
    }

    def detect_from_filename(self, filename: str) -> DocumentType:
        """
        Detect document type from filename extension.

        Args:
            filename: Name of file

        Returns:
            DocumentType enum value

        Raises:
            ValueError: If file type is not supported
        """
        extension = Path(filename).suffix.lower()

        if extension not in self.EXTENSION_MAP:
            raise ValueError(f"Unsupported file type: {extension}")

        return self.EXTENSION_MAP[extension]

    def is_supported(self, filename: str) -> bool:
        """
        Check if file type is supported.

        Args:
            filename: Name of file

        Returns:
            True if supported, False otherwise
        """
        extension = Path(filename).suffix.lower()
        return extension in self.EXTENSION_MAP
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/utils/test_file_type_detector.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add app/utils/file_type_detector.py tests/utils/test_file_type_detector.py
git commit -m "feat: add file type detector for multi-format support"
```

---

## Phase 3: Semantic Chunking Implementation

### Task 7: Create Semantic Chunker Base

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/chunking/semantic_chunker.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/chunking/__init__.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/test_semantic_chunker.py`

**Step 1: Write failing tests**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/test_semantic_chunker.py`:

```python
import pytest
from app.services.chunking.semantic_chunker import SemanticChunker


def test_chunk_simple_text():
    """Test basic text chunking"""
    chunker = SemanticChunker(chunk_size=50, overlap=10)
    text = "This is sentence one. This is sentence two. This is sentence three."

    chunks = chunker.chunk_text(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_chunk_respects_token_limit():
    """Test that chunks don't exceed token limit"""
    chunker = SemanticChunker(chunk_size=100, overlap=20)
    text = "word " * 200  # Create long text

    chunks = chunker.chunk_text(text)

    for chunk in chunks:
        token_count = chunker.count_tokens(chunk)
        # Allow small buffer due to character-to-token estimation
        assert token_count <= 110


def test_chunk_empty_text():
    """Test chunking empty text"""
    chunker = SemanticChunker(chunk_size=50, overlap=10)
    chunks = chunker.chunk_text("")
    assert chunks == []


def test_chunk_with_sections():
    """Test chunking with section context prepended"""
    chunker = SemanticChunker(chunk_size=100, overlap=20)
    text = "This is the main content of the section."
    section_path = "Document > Chapter 1 > Introduction"

    chunks = chunker.chunk_text(text, section_context=section_path)

    assert len(chunks) > 0
    # First chunk should include section context
    assert section_path in chunks[0]


def test_chunk_with_metadata():
    """Test chunk_with_metadata returns proper structure"""
    chunker = SemanticChunker(chunk_size=100, overlap=20)
    text = "This is test content for metadata extraction."

    chunks = chunker.chunk_with_metadata(text)

    assert len(chunks) > 0
    for chunk in chunks:
        assert 'content' in chunk
        assert 'tokens' in chunk
        assert isinstance(chunk['content'], str)
        assert isinstance(chunk['tokens'], int)
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/test_semantic_chunker.py -v`
Expected: FAIL - "No module named 'app.services.chunking'"

**Step 3: Create chunking module directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/chunking`

**Step 4: Create __init__.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/chunking/__init__.py`:

```python
"""Chunking services for document processing."""
from .semantic_chunker import SemanticChunker

__all__ = ['SemanticChunker']
```

**Step 5: Implement semantic chunker**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/chunking/semantic_chunker.py`:

```python
"""Semantic text chunker using recursive splitting."""
from typing import List, Optional, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.token_counter import TokenCounter


class SemanticChunker:
    """
    Semantic text chunker that respects sentence boundaries and provides overlap.
    Uses recursive splitting to preserve semantic coherence.
    """

    def __init__(
        self,
        chunk_size: int = 400,
        overlap: int = 80,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize semantic chunker.

        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap size in tokens
            separators: List of separators for recursive splitting
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.token_counter = TokenCounter()

        # Default separators: paragraph -> newline -> sentence -> word
        if separators is None:
            separators = ["\n\n", "\n", ". ", " ", ""]

        # RecursiveCharacterTextSplitter uses character count
        # Rough approximation: 1 token ≈ 4 characters for English text
        char_chunk_size = chunk_size * 4
        char_overlap = overlap * 4

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=char_chunk_size,
            chunk_overlap=char_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Number of tokens
        """
        return self.token_counter.count_tokens(text)

    def chunk_text(
        self,
        text: str,
        section_context: Optional[str] = None
    ) -> List[str]:
        """
        Chunk text into semantic segments with optional section context.

        Args:
            text: Text to chunk
            section_context: Optional section path to prepend

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # Split text using recursive splitter
        chunks = self.splitter.split_text(text)

        # Prepend section context if provided
        if section_context:
            chunks = [f"[{section_context}]\n\n{chunk}" for chunk in chunks]

        # Filter out empty chunks
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

        return chunks

    def chunk_with_metadata(
        self,
        text: str,
        section_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text and return with metadata.

        Args:
            text: Text to chunk
            section_context: Optional section path

        Returns:
            List of dicts with 'content' and 'tokens' keys
        """
        chunks = self.chunk_text(text, section_context)

        return [
            {
                'content': chunk,
                'tokens': self.count_tokens(chunk)
            }
            for chunk in chunks
        ]
```

**Step 6: Run tests to verify they pass**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/test_semantic_chunker.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add app/services/chunking/ tests/services/test_semantic_chunker.py
git commit -m "feat: implement semantic chunker with overlap and context"
```

---

## Phase 4: Document Processors

### Task 8: Create Base Document Processor Interface

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/base_processor.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/__init__.py`

**Step 1: Create processors directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors`

**Step 2: Create base processor interface**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/base_processor.py`:

```python
"""Base document processor interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentElement:
    """Represents a structured element from a document."""
    content: str
    element_type: str  # paragraph, heading, table, list_item, etc.
    metadata: Dict[str, Any]
    page_number: Optional[int] = None
    section_level: Optional[int] = None
    section_title: Optional[str] = None


@dataclass
class ProcessedDocument:
    """Represents a fully processed document."""
    elements: List[DocumentElement]
    metadata: Dict[str, Any]
    document_type: str


class BaseDocumentProcessor(ABC):
    """Base class for document processors."""

    @abstractmethod
    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process document and extract structured elements.

        Args:
            file_path: Path to document file

        Returns:
            ProcessedDocument with structured elements
        """
        pass

    @abstractmethod
    def supports_file_type(self, file_type: str) -> bool:
        """
        Check if processor supports given file type.

        Args:
            file_type: File type (e.g., 'pdf', 'docx')

        Returns:
            True if supported
        """
        pass
```

**Step 3: Create __init__.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/__init__.py`:

```python
"""Document processors for multi-format support."""
from .base_processor import BaseDocumentProcessor, DocumentElement, ProcessedDocument

__all__ = ['BaseDocumentProcessor', 'DocumentElement', 'ProcessedDocument']
```

**Step 4: Commit**

```bash
git add app/services/processors/
git commit -m "feat: add base document processor interface"
```

---

### Task 9: Create PDF Processor

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/pdf_processor.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_pdf_processor.py`

**Step 1: Create test directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors`

**Step 2: Write failing test**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_pdf_processor.py`:

```python
import pytest
from app.services.processors.pdf_processor import PDFProcessor


def test_pdf_processor_supports_pdf():
    """Test that PDF processor supports PDF files"""
    processor = PDFProcessor()
    assert processor.supports_file_type("pdf") is True
    assert processor.supports_file_type("docx") is False
```

**Step 3: Run test to verify it fails**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/processors/test_pdf_processor.py -v`
Expected: FAIL - "No module named 'app.services.processors.pdf_processor'"

**Step 4: Implement PDF processor**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/pdf_processor.py`:

```python
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
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/processors/test_pdf_processor.py -v`
Expected: Test PASSES

**Step 6: Commit**

```bash
git add app/services/processors/pdf_processor.py tests/services/processors/test_pdf_processor.py
git commit -m "feat: add PDF processor with page tracking"
```

---

### Task 10: Create DOCX Processor

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/docx_processor.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_docx_processor.py`

**Step 1: Write failing test**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_docx_processor.py`:

```python
import pytest
from app.services.processors.docx_processor import DOCXProcessor


def test_docx_processor_supports_docx():
    """Test that DOCX processor supports DOCX files"""
    processor = DOCXProcessor()
    assert processor.supports_file_type("docx") is True
    assert processor.supports_file_type("pdf") is False
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/processors/test_docx_processor.py -v`
Expected: FAIL - Module not found

**Step 3: Implement DOCX processor**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/docx_processor.py`:

```python
"""DOCX document processor."""
from pathlib import Path
from typing import List
from docx import Document
from app.services.processors.base_processor import (
    BaseDocumentProcessor,
    DocumentElement,
    ProcessedDocument
)


class DOCXProcessor(BaseDocumentProcessor):
    """Processor for DOCX documents."""

    def supports_file_type(self, file_type: str) -> bool:
        """Check if this processor supports the file type."""
        return file_type.lower() == "docx"

    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process DOCX and extract structured content.

        Args:
            file_path: Path to DOCX file

        Returns:
            ProcessedDocument with elements preserving structure
        """
        doc = Document(str(file_path))
        elements: List[DocumentElement] = []

        current_section = []
        section_level = 0

        for para in doc.paragraphs:
            if not para.text.strip():
                continue

            # Detect headings by style
            is_heading = para.style.name.startswith('Heading')

            if is_heading:
                # Extract heading level
                try:
                    level = int(para.style.name.split()[-1])
                except:
                    level = 1

                current_section = current_section[:level-1] + [para.text.strip()]
                section_level = level

                element = DocumentElement(
                    content=para.text.strip(),
                    element_type='heading',
                    metadata={'heading_level': level},
                    section_level=level,
                    section_title=' > '.join(current_section)
                )
            else:
                # Regular paragraph
                element = DocumentElement(
                    content=para.text.strip(),
                    element_type='paragraph',
                    metadata={},
                    section_title=' > '.join(current_section) if current_section else None,
                    section_level=section_level
                )

            elements.append(element)

        # Extract tables
        for table_idx, table in enumerate(doc.tables):
            table_text = self._table_to_markdown(table)
            element = DocumentElement(
                content=table_text,
                element_type='table',
                metadata={'table_index': table_idx},
                section_title=' > '.join(current_section) if current_section else None
            )
            elements.append(element)

        metadata = {
            'num_paragraphs': len(doc.paragraphs),
            'num_tables': len(doc.tables),
        }

        return ProcessedDocument(
            elements=elements,
            metadata=metadata,
            document_type='docx'
        )

    def _table_to_markdown(self, table) -> str:
        """Convert table to markdown format."""
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append('| ' + ' | '.join(cells) + ' |')

        if len(rows) > 1:
            # Add header separator
            num_cols = len(table.rows[0].cells)
            separator = '|' + '|'.join(['---'] * num_cols) + '|'
            rows.insert(1, separator)

        return '\n'.join(rows)
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/processors/test_docx_processor.py -v`
Expected: Test PASSES

**Step 5: Commit**

```bash
git add app/services/processors/docx_processor.py tests/services/processors/test_docx_processor.py
git commit -m "feat: add DOCX processor with heading and table support"
```

---

### Task 11: Create Text and Markdown Processor

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/text_processor.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_text_processor.py`

**Step 1: Write failing test**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_text_processor.py`:

```python
import pytest
from pathlib import Path
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/processors/test_text_processor.py -v`
Expected: FAIL - Module not found

**Step 3: Implement text processor**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/text_processor.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/processors/test_text_processor.py -v`
Expected: Tests PASS

**Step 5: Commit**

```bash
git add app/services/processors/text_processor.py tests/services/processors/test_text_processor.py
git commit -m "feat: add text and markdown processor with structure parsing"
```

---

### Task 12: Create CSV Processor

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/csv_processor.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_csv_processor.py`

**Step 1: Write failing test**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_csv_processor.py`:

```python
import pytest
from pathlib import Path
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/processors/test_csv_processor.py -v`
Expected: FAIL - Module not found

**Step 3: Implement CSV processor**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/csv_processor.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/processors/test_csv_processor.py -v`
Expected: Tests PASS

**Step 5: Commit**

```bash
git add app/services/processors/csv_processor.py tests/services/processors/test_csv_processor.py
git commit -m "feat: add CSV processor with header injection"
```

---

## Phase 5: Integration Layer

### Task 13: Create Document Processing Service

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/document_processing_service.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/test_document_processing_service.py`

**Step 1: Write failing tests**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/test_document_processing_service.py`:

```python
import pytest
from pathlib import Path
from app.services.document_processing_service import DocumentProcessingService
from app.models.schemas import DocumentType


def test_get_processor_for_pdf():
    """Test getting processor for PDF"""
    service = DocumentProcessingService()
    processor = service.get_processor(DocumentType.PDF)
    assert processor is not None
    assert processor.supports_file_type("pdf")


def test_get_processor_for_docx():
    """Test getting processor for DOCX"""
    service = DocumentProcessingService()
    processor = service.get_processor(DocumentType.DOCX)
    assert processor is not None
    assert processor.supports_file_type("docx")


def test_get_processor_unsupported():
    """Test getting processor for unsupported type raises error"""
    service = DocumentProcessingService()
    # XLSX not yet registered
    with pytest.raises(ValueError, match="Unsupported document type"):
        service.get_processor(DocumentType.XLSX)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/test_document_processing_service.py -v`
Expected: FAIL - Module not found

**Step 3: Implement document processing service**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/document_processing_service.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api && poetry run pytest tests/services/test_document_processing_service.py -v`
Expected: Tests PASS

**Step 5: Commit**

```bash
git add app/services/document_processing_service.py tests/services/test_document_processing_service.py
git commit -m "feat: add document processing service coordinating processors and chunking"
```

---

### Task 14: Update Document Upload Endpoint

**Files:**
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/document_service.py`

**Step 1: Read current document service**

Run: `cat /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/document_service.py | head -100`
Review current implementation to understand structure

**Step 2: Update document service imports**

Add to top of `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/document_service.py`:

```python
from app.services.document_processing_service import DocumentProcessingService
from app.utils.file_type_detector import FileTypeDetector
```

**Step 3: Update DocumentService __init__ method**

Replace or update the `__init__` method in `DocumentService` class:

```python
def __init__(self, db: AsyncSession):
    self.db = db
    self.processing_service = DocumentProcessingService()
    self.file_detector = FileTypeDetector()
```

**Step 4: Update upload_document method**

Replace the upload_document method to use new processing pipeline:

```python
async def upload_document(
    self,
    file: UploadFile,
    title: str,
    description: Optional[str],
    upload_dir: Path
) -> Document:
    """Upload and process document with semantic chunking."""

    # Detect file type
    try:
        document_type = self.file_detector.detect_from_filename(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save file
    file_id = uuid.uuid4()
    file_path = upload_dir / f"{file_id}_{file.filename}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create document record
    document = Document(
        id=file_id,
        title=title,
        description=description,
        file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        file_path=str(file_path),
        document_type=document_type.value,
        upload_status="processing",
        embedding_status="pending"
    )

    self.db.add(document)
    await self.db.commit()
    await self.db.refresh(document)

    # Process and chunk document
    try:
        chunks_data = self.processing_service.process_and_chunk(
            file_path,
            document_type
        )

        # Create chunk records
        for idx, chunk_data in enumerate(chunks_data):
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=document.id,
                chunk_index=idx,
                chunk_text=chunk_data['content'],
                token_count=chunk_data.get('tokens'),
                section_title=chunk_data.get('section_title'),
                section_level=chunk_data.get('section_level', 0),
                page_number=chunk_data.get('page_number'),
                chunk_tokens=chunk_data.get('tokens'),
                chunk_metadata=chunk_data.get('metadata', {})
            )
            self.db.add(chunk)

        document.upload_status = "completed"
        await self.db.commit()

        return document

    except Exception as e:
        document.upload_status = "failed"
        await self.db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )
```

**Step 5: Add missing imports if needed**

Ensure these imports are at the top of the file:

```python
import uuid
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentChunk
```

**Step 6: Commit**

```bash
git add app/services/document_service.py
git commit -m "feat: integrate new document processing pipeline in upload"
```

---

### Task 15: Update Search Endpoint for Metadata

**Files:**
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/search_service.py`

**Step 1: Read current search service**

Run: `cat /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/search_service.py`
Review current search implementation

**Step 2: Update search method to include metadata**

Replace or update the search method in `SearchService` class:

```python
async def search(
    self,
    query: str,
    limit: int = 10,
    document_ids: Optional[List[UUID]] = None
) -> List[SearchResultItem]:
    """
    Search documents with enriched metadata.

    Args:
        query: Search query
        limit: Number of results
        document_ids: Optional filter by document IDs

    Returns:
        List of search results with metadata
    """
    # Get query embedding from embedder service
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.embedder_url}/embed/query",
            json={"query": query}
        )
        response.raise_for_status()
        query_vector = response.json()["embedding"]

    # Search Qdrant
    search_results = self.qdrant_client.search(
        collection_name="documents",
        query_vector=query_vector,
        limit=limit
    )

    # Get chunk IDs from results
    chunk_ids = [UUID(result.payload["chunk_id"]) for result in search_results]

    # Join with PostgreSQL to get full metadata
    query = (
        select(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(DocumentChunk.id.in_(chunk_ids))
    )

    result = await self.db.execute(query)
    chunks_with_docs = {str(chunk.id): (chunk, doc) for chunk, doc in result}

    # Build enriched results
    enriched_results = []
    for search_result in search_results:
        chunk_id = search_result.payload["chunk_id"]
        if chunk_id in chunks_with_docs:
            chunk, doc = chunks_with_docs[chunk_id]

            enriched_results.append(SearchResultItem(
                chunk_id=chunk.id,
                document_id=doc.id,
                document_title=doc.title,
                chunk_text=chunk.chunk_text,
                chunk_index=chunk.chunk_index,
                score=search_result.score,
                section_title=chunk.section_title,
                page_number=chunk.page_number,
                chunk_metadata=chunk.chunk_metadata or {}
            ))

    return enriched_results
```

**Step 3: Add missing imports**

Ensure these imports are at the top:

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from app.models.document import Document, DocumentChunk
from app.models.schemas import SearchResultItem
```

**Step 4: Commit**

```bash
git add app/services/search_service.py
git commit -m "feat: enrich search results with chunk metadata"
```

---

## Phase 6: Optional Format Processors

### Task 16: Add XLSX Processor (Optional)

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/xlsx_processor.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/services/processors/test_xlsx_processor.py`
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/document_processing_service.py`

**Step 1: Write failing test**

Create test file with support check test.

**Step 2: Implement XLSX processor**

Create processor with openpyxl integration to read sheets and convert rows to searchable text.

**Step 3: Register in DocumentProcessingService**

Add `DocumentType.XLSX: XLSXProcessor()` to processors dict.

**Step 4: Test and commit**

Run tests, verify, commit with message: "feat: add Excel (XLSX) processor"

---

### Task 17: Add PPTX Processor (Optional)

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/pptx_processor.py`
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/document_processing_service.py`

**Step 1: Implement PPTX processor**

Create processor using python-pptx to extract slide text with slide numbers.

**Step 2: Register processor**

Add to DocumentProcessingService.

**Step 3: Commit**

Commit with message: "feat: add PowerPoint (PPTX) processor"

---

### Task 18: Add HTML Processor (Optional)

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/processors/html_processor.py`
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/services/document_processing_service.py`

**Step 1: Implement HTML processor**

Create processor using BeautifulSoup to extract structured content from HTML.

**Step 2: Register processor**

Add to DocumentProcessingService.

**Step 3: Commit**

Commit with message: "feat: add HTML processor"

---

## Phase 7: Database & Testing

### Task 19: Apply Database Migration

**Files:**
- Run: Database migration script

**Step 1: Check if database is running**

Run: `docker ps | grep postgres`
Expected: PostgreSQL container running (or start docker-compose if not)

**Step 2: Apply migration**

Run: `docker exec -i raas-postgres psql -U raasuser -d raasdb < /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/app/migrations/003_add_chunk_metadata.sql`
Expected: Migration applied successfully

**Step 3: Verify schema changes**

Run: `docker exec -it raas-postgres psql -U raasuser -d raasdb -c "\d document_chunks"`
Expected: See new columns (section_title, section_level, page_number, chunk_tokens, parent_chunk_id, chunk_metadata)

**Step 4: Document completion**

```bash
echo "Migration 003 applied at $(date)" >> migration_log.txt
git add migration_log.txt
git commit -m "docs: record migration 003 applied successfully"
```

---

### Task 20: Create Integration Test

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/integration/test_full_workflow.py`

**Step 1: Create integration test directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/api/tests/integration`

**Step 2: Write integration test**

Create comprehensive test covering upload → process → search workflow with metadata validation.

**Step 3: Run integration test**

Verify full pipeline works end-to-end.

**Step 4: Commit**

Commit with message: "test: add integration test for document processing workflow"

---

## Phase 8: Frontend Updates

### Task 21: Update Frontend Types

**Files:**
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/frontend/src/types/index.ts`

**Step 1: Add metadata fields to SearchResult**

Update the `SearchResult` interface:

```typescript
export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_title: string;
  chunk_text: string;
  chunk_index: number;
  score: number;
  section_title?: string;
  page_number?: number;
  chunk_metadata?: Record<string, any>;
}
```

**Step 2: Add metadata fields to DocumentChunk**

Update the `DocumentChunk` interface:

```typescript
export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  chunk_text: string;
  token_count: number | null;
  section_title?: string;
  section_level?: number;
  page_number?: number;
  chunk_tokens?: number;
  chunk_metadata?: Record<string, any>;
  created_at: string;
}
```

**Step 3: Commit**

```bash
git add src/types/index.ts
git commit -m "feat: add metadata fields to frontend types"
```

---

### Task 22: Update Search Results Display

**Files:**
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/frontend/src/components/SearchResults.tsx` (or similar)

**Step 1: Find search results component**

Run: `find /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/frontend/src -name "*earch*" -type f`
Identify the component that renders search results.

**Step 2: Add metadata display**

Add section title and page number display to result cards:

```typescript
{result.section_title && (
  <div className="text-sm text-blue-600 mb-2">
    📍 {result.section_title}
  </div>
)}

{result.page_number && (
  <div className="text-sm text-gray-500 mb-2">
    Page {result.page_number}
  </div>
)}
```

**Step 3: Test frontend**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/frontend && npm run dev`
Test search UI displays metadata correctly.

**Step 4: Commit**

```bash
git add src/components/
git commit -m "feat: display section and page metadata in search results"
```

---

## Phase 9: Verification

### Task 23: End-to-End Verification

**Files:**
- Manual testing and verification

**Step 1: Start all services**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/docker-compose && docker-compose up -d`

**Step 2: Upload test documents**

Test with multiple file types:
- PDF file
- DOCX file with headings
- Markdown file
- CSV file

**Step 3: Verify chunks in database**

Run: `docker exec -it raas-postgres psql -U raasuser -d raasdb -c "SELECT id, section_title, page_number, chunk_tokens FROM document_chunks LIMIT 10;"`
Expected: See metadata populated

**Step 4: Test search with metadata**

Use frontend or API to search and verify results include section titles and page numbers.

**Step 5: Document completion**

Create implementation completion document:

```bash
cat > IMPLEMENTATION_COMPLETE.md << 'EOF'
# Semantic Chunking Implementation Complete

## Features Implemented
- ✅ Database schema with metadata fields (migration 003)
- ✅ Multi-format document support (PDF, DOCX, TXT, MD, CSV, XLSX, PPTX, HTML)
- ✅ Semantic chunking (400-token chunks, 80-token overlap)
- ✅ Section hierarchy preservation with context prepending
- ✅ Rich metadata storage in PostgreSQL
- ✅ Enhanced search results with section titles and page numbers
- ✅ Frontend display of metadata

## Testing
- Unit tests: All processors, chunker, utilities
- Integration tests: Full upload → process → search workflow
- Manual E2E testing: Verified with multiple document types

## Architecture
- Modular processor design (easy to add new formats)
- Separation of concerns (processors, chunking, service coordination)
- Token-aware chunking with overlap
- Metadata stored in PostgreSQL, minimal payloads in Qdrant

Completed: $(date)
EOF

git add IMPLEMENTATION_COMPLETE.md
git commit -m "docs: mark semantic chunking implementation complete"
```

---

## Summary

This plan completes the remaining 18 tasks (6-23) from the semantic chunking implementation:

**Phase 2-3**: File detection, semantic chunking
**Phase 4**: Document processors (PDF, DOCX, TXT/MD, CSV, XLSX, PPTX, HTML)
**Phase 5**: Integration (processing service, upload/search endpoints)
**Phase 6**: Optional processors (XLSX, PPTX, HTML)
**Phase 7**: Database migration and testing
**Phase 8**: Frontend updates
**Phase 9**: E2E verification

**Estimated Time**: 2-3 days for core features (Tasks 6-15), +4-6 hours for optional formats and frontend

**Execution Options**:
1. **Subagent-Driven (recommended)**: Use superpowers:subagent-driven-development to dispatch fresh subagent per task with code review between tasks
2. **Manual Execution**: Follow tasks sequentially with TDD methodology
3. **Parallel Session**: Use superpowers:executing-plans in a dedicated worktree
