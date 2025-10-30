# Screenshots Guide

This directory contains screenshots and images for the project README and documentation.

## Required Screenshots

To complete the README, capture the following screenshots:

### 1. Search Interface (Hero Image)
**Filename**: `search-interface.png`

**What to capture**:
- Full search page showing search bar, results, and AI summary
- Should show actual search results with at least 3-4 results
- Include the AI-generated summary with citations [1] [2]
- Make sure UI looks polished (no errors, clean state)

**How to capture**:
1. Start services: `docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d`
2. Upload 2-3 documents via UI or API
3. Perform a search like "What is machine learning?"
4. Wait for AI summary to load
5. Take screenshot of full browser window (Cmd+Shift+4 on macOS)
6. Save as `search-interface.png`

### 2. Document Upload
**Filename**: `document-upload.png`

**What to capture**:
- Document upload modal or page
- Show the file picker or drag-and-drop area
- Or show the documents list with several uploaded documents

**How to capture**:
1. Navigate to http://localhost:3000
2. Click upload button
3. Capture the upload modal/interface
4. Save as `document-upload.png`

### 3. Search Demo (Animated GIF)
**Filename**: `search-demo.gif`

**What to capture**:
- User typing in search bar
- Results appearing
- AI summary generating
- Total: 5-10 seconds

**How to capture**:
1. Use screen recording tool (QuickTime, OBS, or online tool)
2. Record: typing query → results load → summary appears
3. Convert to GIF using online tool (ezgif.com, gifski)
4. Optimize to <5MB
5. Save as `search-demo.gif`

### 4. Architecture Diagram (Optional Enhancement)
**Filename**: `architecture.png`

**What to create**:
- Visual diagram of microservices architecture
- Use draw.io, Excalidraw, or similar
- Show: Frontend → API → Embedder/Search/Generator → Databases
- Export as PNG

## Optional Screenshots

### API Documentation
**Filename**: `api-docs.png`
- Screenshot of http://localhost:8000/docs (Swagger UI)

### Kubernetes Dashboard
**Filename**: `k8s-pods.png`
- `kubectl get pods -n raas` output or K8s dashboard

### Database/Qdrant
**Filename**: `qdrant-collection.png`
- Qdrant dashboard showing document collection

## Image Specifications

- **Format**: PNG for screenshots, GIF for animations
- **Resolution**: 1200-1600px wide (for good GitHub rendering)
- **File Size**: <2MB for PNG, <5MB for GIF
- **Naming**: kebab-case (lowercase with hyphens)
- **Optimization**: Use TinyPNG, ImageOptim, or similar

## Quick Capture Commands

### Start Services
```bash
cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Wait 30 seconds, then check:
curl http://localhost:8000/health
curl http://localhost:3000
```

### Upload Sample Documents
```bash
# Upload a sample document
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@example-documents/machine-learning-introduction.docx" \
  -F "title=Machine Learning Introduction"

curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@example-documents/semantic-search-overview.txt" \
  -F "title=Semantic Search Overview"
```

### Test Search
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "limit": 5,
    "model": "openai:gpt-4o-mini"
  }'
```

Or use the UI at http://localhost:3000

## After Capturing Screenshots

1. Save images to this directory
2. Optimize file sizes
3. Update main README.md with image references
4. Test image rendering on GitHub (push and view)

## Example README Usage

```markdown
## Demo

![Search Interface](docs/images/search-interface.png)
*Semantic search with AI-powered summaries and citation tracking*

![Search Demo](docs/images/search-demo.gif)
*Real-time document search and answer generation*
```

## Notes

- **Git LFS**: Not needed for a few small images (<5MB each)
- **Privacy**: Don't include sensitive data in screenshots
- **Quality**: Use high-DPI displays for crisp screenshots
- **Context**: Capture enough UI to show functionality clearly
