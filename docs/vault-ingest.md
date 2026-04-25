# Vault Ingest — Document Conversion

Convert any document to Markdown and drop it into your vault inbox with proper frontmatter.

Built on [Microsoft MarkItDown](https://github.com/microsoft/markitdown) (MIT, 114k+ stars).

## Supported Formats

PDF, DOCX, PPTX, XLSX, XLS, HTML, CSV, JSON, XML, MSG, EML, EPUB, IPYNB, ZIP (recursive).

## Install

```bash
pip install 'markitdown[pdf,docx,pptx,xlsx]'
```

## Usage

```bash
python scripts/vault-ingest.py <file> [flags]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--tags` | (auto) | Comma-separated extra tags |
| `--privacy` | 2 | Privacy level 1-4 |
| `--status` | draft | draft/active/review/done |
| `--dest` | 00-inbox/ | Destination dir (relative to vault root) |
| `--name` | (filename) | Custom output filename (without .md) |
| `--stdout` | false | Write to stdout instead of file |

### Examples

```bash
# RFP to inbox
python scripts/vault-ingest.py rfp.pdf --tags work/project --privacy 2

# Contract to private
python scripts/vault-ingest.py contract.pdf --privacy 3 --dest _private/contracts/

# PowerPoint deck
python scripts/vault-ingest.py demo.pptx --tags work/fia --status active

# Excel to stdout (inspect before saving)
python scripts/vault-ingest.py budget.xlsx --stdout
```

## Automatic Behaviors

- **Tags:** `source/pdf`, `source/docx` etc added automatically based on file extension
- **Privacy 3-4:** Routed to `_private/` automatically if `--dest` is not specified
- **Collision handling:** Timestamp suffix if file already exists
- **Frontmatter:** Generated with tags, status, created, privacy, source_file

## As a Larry Skill

Add to your skills INDEX with these triggers:
- "convert this file to markdown"
- "import document into vault"
- "put this PDF/Word/PowerPoint into inbox"
- "analyze this document" (convert first, then read)

## Python API (Direct)

```python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("path/to/file.pptx")
print(result.text_content)
```

## What It Does NOT Do

- Images (that's your image agent)
- Audio transcription (that's your audio agent)
- Semantic indexing (that's your memory system, run after ingestion)
