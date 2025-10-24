#!/usr/bin/env python3
"""Upload test corpus documents to RAAS."""
import os
import requests
from pathlib import Path
import json

# Configuration
API_URL = "http://localhost:8000/api/v1"
CORPUS_DIR = Path(__file__).parent / "data" / "rag_test_corpus"

def upload_document(file_path: Path):
    """Upload a single document to RAAS."""
    # Prepare the file
    with open(file_path, 'rb') as f:
        files = {
            'file': (file_path.name, f, 'application/octet-stream')
        }
        # Prepare form data
        data = {
            'title': file_path.stem.replace('_', ' ').title(),
            'description': f'Test document from corpus: {file_path.name}'
        }

        # Upload
        print(f"Uploading {file_path.name}...", end=' ')
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            data=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ (ID: {result['id']})")
            return result
        else:
            print(f"✗ ({response.status_code})")
            print(f"  Error: {response.text}")
            return None

def main():
    """Upload all documents from the test corpus."""
    # Check if corpus directory exists
    if not CORPUS_DIR.exists():
        print(f"Error: Corpus directory not found: {CORPUS_DIR}")
        return

    # Get all document files (txt, docx, pdf)
    files = sorted([
        f for f in CORPUS_DIR.glob("*")
        if f.suffix.lower() in ['.txt', '.docx', '.pdf']
    ])

    print(f"Found {len(files)} documents to upload\n")

    # Upload each file
    results = []
    for file_path in files:
        result = upload_document(file_path)
        if result:
            results.append(result)

    print(f"\n{'='*60}")
    print(f"Upload complete: {len(results)}/{len(files)} documents uploaded successfully")

    # Save results
    results_file = Path(__file__).parent / "upload_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {results_file}")

if __name__ == "__main__":
    main()
