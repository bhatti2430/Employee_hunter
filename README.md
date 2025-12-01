# Employee Hunter AI

A Flask-based web application for CV intake, AI extraction, and intelligent candidate matching using similarity search. Upload CVs, search by job description, and get matched candidates ranked by relevance.

## Features

- **CV Upload & Parsing**: Support for PDF, DOCX, DOC, and TXT files with multi-layer extraction (pdfplumber → PyPDF2 → raw fallback)
- **AI-Powered Extraction**: Uses OpenAI GPT-3.5-turbo or Claude Haiku 4.5 to extract:
  - Personal info (name, email, phone, address, location)
  - Professional info (role, experience, company, summary)
  - Education (degree, university, qualifications)
  - Technical skills (languages, frameworks, databases, cloud platforms)
- **Intelligent Search**: TF-IDF + cosine similarity matching to find best candidate fits
- **Scalable Database**: ChromaDB persistent storage with server-side metadata fetching
- **Provider Switching**: Easy toggle between OpenAI and Claude via `LLM_PROVIDER` env var
- **Robust Fallbacks**: Enhanced local extractors kick in if LLM calls fail or return malformed JSON

## Project Structure

```
employee_hunter_ai/
├── app.py                              # Flask entrypoint: routes, session handling
├── config.py                           # Environment variables, helpers
├── requirements.txt                    # Pinned dependencies
├── README.md                           # This file
├── cv_database/                        # ChromaDB persistent storage (auto-created)
│   └── chroma.sqlite3
├── static/
│   └── uploads/                        # Uploaded CV files (temporary)
├── templates/
│   ├── index.html                      # Home page
│   ├── upload.html                     # CV upload form
│   ├── results.html                    # Search results grid
│   └── candidate_profile.html          # Detailed candidate profile
├── src/
│   ├── core/
│   │   └── ai_matcher.py               # Pipeline orchestration
│   ├── database/
│   │   └── chroma_db.py                # ChromaDB wrapper + TF-IDF search
│   ├── llm/
│   │   ├── openai_client.py            # OpenAI ChatCompletion integration
│   │   ├── claude_client.py            # Claude (Anthropic) HTTP client
│   │   ├── cv_analyzer.py              # (legacy, optional)
│   │   └── skills_extractor.py         # (legacy, optional)
│   └── utils/
│       ├── file_parser.py              # PDF/DOCX/TXT extraction
│       └── text_cleaner.py             # Text normalization
```

## Quick Start

### 1. Prerequisites
- Python 3.10+ (tested with 3.14.0)
- Git (optional, for version control)

### 2. Installation

Clone or download the repo and navigate to the project root:

```bash
cd employee_hunter_ai
```

Create and activate a virtual environment:

```powershell
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/Mac bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root with your API keys:

```plaintext
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
LLM_PROVIDER=openai
```

**Options for `LLM_PROVIDER`:**
- `openai` (default) — Uses OpenAI GPT-3.5-turbo for extraction
- `claude` — Uses Claude Haiku 4.5 from Anthropic for extraction

If `ANTHROPIC_API_KEY` is not set and `LLM_PROVIDER=claude`, the app will fall back to OpenAI.

### 4. Run the App

```bash
python app.py
```

The app will start on **http://0.0.0.0:5000** (or http://localhost:5000 in your browser).

## Usage

### Upload CVs

1. Go to **"Upload CV"** in the navigation
2. Select a candidate name and upload a PDF/DOCX/DOC/TXT file
3. The app will:
   - Parse the file to extract text
   - Clean and normalize the text
   - Send to LLM for comprehensive analysis
   - Store metadata and raw CV in the database
4. You'll see a confirmation with detected skills and metadata

### Search & Match

1. Go to **"Search"** (home page)
2. Paste a job description (e.g., "Looking for a Python developer with AWS experience")
3. Click **"Find Matching Candidates"**
4. Results show all matching CVs ranked by relevance (65–95% match score)
5. Click any candidate card to view the full profile with:
   - Contact info (email, phone, address)
   - Professional experience and current role
   - Education and certifications
   - Technical skills by category
   - CV preview (first 800 characters)

### Debug & Inspection

Use these debug endpoints to inspect the database:

- **`GET /debug/database`** — Full database contents (CV IDs, names, skills)
- **`GET /debug/cv_count`** — Total number of stored CVs
- **`GET /debug/clear_database`** — Clear all stored CVs (⚠️ destructive)

Example:

```bash
curl http://localhost:5000/debug/cv_count
# Output: {"total_cvs": 5}
```

## Data Flow

```
Upload CV
    ↓
Parse file (pdfplumber → PyPDF2 → raw)
    ↓
Clean text (normalize, remove special chars)
    ↓
LLM Analysis (OpenAI or Claude)
    ├→ extract_skills()
    └→ extract_comprehensive_details() → JSON schema
    ↓
Format metadata (education, summary, preview)
    ↓
Store in ChromaDB + session
    ↓
[Database Ready]

Search Job Description
    ↓
TF-IDF vectorization + cosine similarity
    ↓
Filter by threshold (0.15)
    ↓
Remap scores to 65–95% range
    ↓
Return ranked results
    ↓
Store IDs + distances in session
    ↓
[Results Ready]

Click Candidate
    ↓
Fetch metadata from DB by ID
    ↓
Render profile page
    ↓
[Profile Loaded - Always correct data]
```

## Metadata Keys

When a CV is stored, the following metadata is extracted and available:

| Key | Description |
|-----|-------------|
| `candidate_name` | Full name of candidate |
| `email` | Email address |
| `phone` | Phone number with country code |
| `address` | Full postal address |
| `location` | City, country |
| `current_role` | Current job title |
| `experience` | Years of experience (e.g., "5 years") |
| `current_company` | Current employer name |
| `education` | Highest degree + university (bullet points) |
| `summary` | Professional summary (bullet points) |
| `programming_languages` | Comma-separated list |
| `frameworks` | Comma-separated list |
| `databases` | Comma-separated list |
| `cloud_platforms` | Comma-separated list |
| `skills` | Comma-separated list of all skills |
| `raw_text` | First ~800 chars of CV (formatted preview) |

## Search Configuration

To adjust search recall/precision, edit `src/database/chroma_db.py`:

```python
# Line ~80 in chroma_db.py
threshold = 0.15  # Increase for stricter matching, decrease for looser
max_features = 1000  # Reduce for fewer features (faster but less accurate)
```

Score remapping (65–95%) happens on lines ~95-98:

```python
score = 65 + (sim * 30)  # Adjust constants to change range
```

## LLM Integration

### OpenAI (Default)

- **Model**: `gpt-3.5-turbo`
- **Max tokens**: 800 (skills), 1500 (comprehensive)
- **Temperature**: 0.3 (skills), 0.1 (comprehensive)
- **Fallback**: Enhanced local regex + pattern matching if LLM fails

### Claude (Anthropic)

- **Model**: `claude-haiku-4.5`
- **API**: HTTP POST to `https://api.anthropic.com/v1/complete`
- **Max tokens**: Same as OpenAI
- **Temperature**: Same as OpenAI
- **Fallback**: Automatically calls `OpenAIClient` enhanced extractors

**To use Claude:**

1. Set `ANTHROPIC_API_KEY` in `.env`
2. Set `LLM_PROVIDER=claude` in `.env`
3. Restart the app

The app will switch seamlessly at runtime.

## Troubleshooting

### "No candidate data available. Please perform a search first."

**Cause**: Session cookie was too large and truncated (when >3 CVs in results).

**Fix** (already applied): Session now stores only lightweight IDs + distances. Metadata is fetched server-side by ID on profile load.

**What to do**:
1. Clear browser cookies for localhost:5000
2. Restart the app
3. Re-run your search

### "ModuleNotFoundError: No module named 'chromadb'"

**Cause**: Dependencies not installed in the active venv.

**Fix**:
```bash
.venv\Scripts\Activate.ps1    # Ensure venv is active
pip install -r requirements.txt
```

### "OPENAI_API_KEY not set"

**Cause**: Missing or incorrect API key in `.env`.

**Fix**:
1. Create/edit `.env` in project root
2. Add: `OPENAI_API_KEY=sk-your-key`
3. Save and restart the app

### Search returns no results

**Cause**: Job description too different from CV content, or similarity threshold too high.

**Fix**:
1. Try a simpler job description (e.g., "Python developer" instead of very specific requirements)
2. Lower the threshold in `src/database/chroma_db.py` (line ~80: `threshold = 0.10`)
3. Ensure CVs are uploaded and database contains data: `GET /debug/cv_count`

### Profile shows "Email in CV" for all candidates

**Cause**: LLM extraction failed; fallback regex didn't find valid email.

**Fix**: 
1. Check server logs for OpenAI errors
2. Verify CV file is readable (try uploading a test PDF)
3. Check that OPENAI_API_KEY is valid

## Dependencies

See `requirements.txt` for full list. Key packages:

- **flask** 2.3.3 — Web framework
- **chromadb** 0.4.15 — Vector database
- **openai** 1.3.0 — OpenAI API client
- **pdfplumber** 0.9.0 — PDF extraction
- **PyPDF2** 3.0.1 — PDF fallback
- **scikit-learn** 1.5.2 — TF-IDF + cosine similarity
- **requests** 2.32.3 — HTTP client (for Claude)
- **python-dotenv** 1.0.0 — .env parsing

## Performance Notes

- **First search** may be slow (TF-IDF vectorization on all CVs)
- **Subsequent searches** are faster (vectorizer is cached in memory)
- **Profile load** is instant (direct DB lookup by ID)
- **Large CV count** (100+): Consider batch uploads or async processing (future enhancement)

## Future Enhancements

- Async CV processing queue (Celery + Redis)
- Resume screening via LLM (ranking by custom criteria)
- Bulk upload with progress tracking
- Export search results to CSV
- User authentication + multi-user support
- API rate limiting and caching
- Mobile app

## Support & Debugging

For detailed debugging, enable logs in `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

Check console output for:
- ✅ CV stored permanently
- 🔍 Search completed. Found X candidates
- 👤 Loading profile for index: N
- ❌ Error messages with traceback

## License

This project is provided as-is. Modify and distribute freely.

## Authors

- AI-enhanced by Claude Haiku 4.5 (Anthropic)
- Built with Flask, ChromaDB, OpenAI/Claude, scikit-learn

---

**Version**: 1.0.0  
**Last Updated**: November 28, 2025
