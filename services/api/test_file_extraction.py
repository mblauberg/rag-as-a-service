"""Quick test to verify file extraction works for all types."""
import asyncio
from pathlib import Path
from app.infrastructure.processing.file_processor import FileProcessorImpl

async def test_extraction():
    processor = FileProcessorImpl()
    test_dir = Path(__file__).parent.parent.parent / "data" / "rag_test_corpus"
    
    files_to_test = [
        ("doc_01.txt", "txt"),
        ("doc_pdf_01.pdf", "pdf"),
        ("doc_docx_01.docx", "docx"),
        ("doc_md_01.md", "md"),
        ("doc_csv_01.csv", "csv"),
    ]
    
    for filename, file_type in files_to_test:
        file_path = test_dir / filename
        if not file_path.exists():
            print(f"❌ {filename}: File not found")
            continue
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            text = await processor.extract_text(content, file_type)
            
            if text and len(text) > 0:
                print(f"✅ {filename}: Extracted {len(text)} chars")
                print(f"   Preview: {text[:100]}...")
            else:
                print(f"⚠️  {filename}: Extracted but empty")
                
        except Exception as e:
            print(f"❌ {filename}: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
