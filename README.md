# 📚 Resume Parser

**Content Overview:**
Build a resume parsing system that extracts key information from uploaded resumes (PDF/DOCX Format) and displays the results through both a REST API and web interface.

## 1. Pre-requisites
1. Create an environment and activate it
```bash
python -m venv .venv
.venv\Scripts\Activate
```

2. Install the dependencies
```bash
pip install uv
uv pip install -r requirements.txt --prerelease=allow
```

3. Configure environment variables
```bash
cp .env.example .env
```

The defaults work in `.env` to change the model or port number:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3
OLLAMA_TIMEOUT=300
API_BASE_URL=http://localhost:8000
```

4. Install Ollama in local machine - Run locally
Download from **https://ollama.com/download/** and install for your OS (MacOS, Linux, Windows)
```bash
# Verify installation
ollama --version
```

5. Pull a free model download
```bash
ollama pull phi3
```

## 2. Start FastAPI backend
```bash
uvicorn app.main:app --reload --port 8000
```

API running at `http://localhost:8000` — docs at `http://localhost:8000/docs`

## 3. Start Streamlit UI
Open another **terminal**:
```bash
streamlit run ui/streamlit_app.py
```

UI available at `http://localhost:8501`

---

## 📡 API Reference

### `POST /api/upload`

Upload and parse a resume file.

**Request** — `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | File | PDF or DOCX resume |

**Response `200 OK`**

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "resume": {
    "contact": {
      "name": "Aaron P",
      "email": "aaronperiyasamy@gmail.com",
      "phone": "+91 98849 45214",
      "location": "Chennai, India",
      "linkedin": "https://linkedin.com/in/aaron-p-80135911b",
      "github": "https://github.com/aaronp07/aaronp07",
      "youtube": null,
      "website": null
    },
    "summary": "Generative AI engineer with 5 years experience…",
    "work_experience": [
      {
        "company": "Syntel India Pvt Ltd",
        "role": "Senior Generative AI Engineer",
        "duration": "July 2017 – April 2026",
        "location": "Remote",
        "responsibilities": [
          "Led backend API development in FastAPI with RAG"
        ]
      }
    ],
    "education": [
      {
        "degree": "MCA",
        "institution": "Madras University",
        "year": "2025"
      }
    ],
    "skills": {
      "technical": ["Python", "FastAPI", "PostgreSQL", "LangChain", "LangGraph"],
      "languages": ["Python", "JavaScript", "English", "Tamil"]
    },
    "certifications": [
      { "name": "Azure AI 900", "issuer": "Microsoft", "year": "2025" }
    ],
    "raw_text_length": 4210
  }
}
```

**Error responses**

| Code | Reason |
|---|---|
| `400` | Empty file |
| `415` | Unsupported file type (only PDF/DOCX) |
| `422` | Text extraction or JSON parsing failed |
| `503` | Ollama is not running or not reachable |
| `500` | Internal server error |

---

### `GET /api/resume/{document_id}`

Retrieve a previously parsed resume.

**Response `200 OK`** — same schema as the `resume` object above.  
**Response `404 Not Found`** — unknown document ID.

---

## 🧪 Testing with curl

```bash
# Upload
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/resume.pdf"

# Retrieve
curl http://localhost:8000/api/resume/<document_id>
```

---

## 🏗️ Architecture

```
Browser / Streamlit UI
        │
        │  multipart/form-data POST /api/upload
        ▼
  FastAPI Backend (app/main.py)
        │
        ├── ResumeParserService (services/parser.py)
        │       ├── PyMuPDF   → PDF  → raw text
        │       └── python-docx → DOCX → raw text
        │
        └── LLMService (services/llm_service.py)
                │  HTTP POST /api/generate
                ▼
         Ollama (localhost:11434)
                │  runs mistral / llama3 / phi3 / …
                ▼
         Structured JSON → Pydantic models → API response
```