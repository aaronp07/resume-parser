"""
Streamlit UI for the Resume Parser — powered by Ollama (local, free LLM).
Run with: streamlit run ui/streamlit_app.py
"""

import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Parser · Ollama",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif; }
.hero { text-align:center; padding:2.2rem 0 1.2rem; }
.hero h1 { font-size:2.8rem; color:#1a1a2e; margin-bottom:.2rem; }
.hero p { color:#6b7280; font-size:1.05rem; }
.card { background:#fff; border:1px solid #e5e7eb; border-radius:12px;
        padding:1.3rem 1.5rem; margin-bottom:1rem;
        box-shadow:0 1px 3px rgba(0,0,0,.06); }
.card-header { display:flex; align-items:center; gap:.5rem; font-size:1.05rem;
               font-weight:600; color:#1a1a2e; margin-bottom:.8rem;
               border-bottom:2px solid #f3f4f6; padding-bottom:.6rem; }
.badge        { display:inline-block; background:#eef2ff; color:#4f46e5;
                border-radius:6px; padding:2px 10px; font-size:.82rem;
                font-weight:500; margin:3px 3px 3px 0; }
.badge-green  { background:#ecfdf5; color:#059669; }
.badge-orange { background:#fff7ed; color:#d97706; }
.badge-purple { background:#f5f3ff; color:#7c3aed; }
.doc-id { font-family:monospace; font-size:.78rem; color:#9ca3af;
          background:#f9fafb; border-radius:4px; padding:2px 6px; }
.stButton>button { background:#4f46e5; color:#fff; border:none;
                   border-radius:8px; font-weight:600; padding:.5rem 1.3rem;
                   font-size:1rem; transition:background .2s; }
.stButton>button:hover { background:#3730a3; }
.work-entry { border-left:3px solid #4f46e5; padding-left:1rem; margin-bottom:1.1rem; }
.edu-entry  { border-left:3px solid #059669; padding-left:1rem; margin-bottom:1.1rem; }
.pill-ok  { display:inline-block; background:#dcfce7; color:#15803d;
            border-radius:999px; padding:2px 12px; font-size:.82rem; font-weight:600; }
.pill-err { display:inline-block; background:#fee2e2; color:#dc2626;
            border-radius:999px; padding:2px 12px; font-size:.82rem; font-weight:600; }
li { margin-bottom:.25rem; }
</style>
""", unsafe_allow_html=True)

# Sidebar - Ollama status & model picker
with st.sidebar:
    st.markdown("## ⚙️ Ollama Settings")

    ollama_url = st.text_input("Ollama URL", value=OLLAMA_BASE)
    model_input = st.text_input("Model", value=OLLAMA_MODEL,
                                help="Must be pulled locally first (e.g. `ollama pull mistral`)")

    st.markdown("---")
    st.markdown("**Status**")

    # Check Ollama health
    try:
        tags_resp = requests.get(f"{ollama_url}/api/tags", timeout=4)
        available = [m["name"] for m in tags_resp.json().get("models", [])]
        st.markdown('<span class="pill-ok">🟢 Ollama online</span>', unsafe_allow_html=True)
        if available:
            st.caption("Pulled models:\n" + "\n".join(f"• {m}" for m in available))
        else:
            st.warning("No models pulled yet. Run:\n```\nollama pull mistral\n```")
    except Exception:
        st.markdown('<span class="pill-err">🔴 Ollama offline</span>', unsafe_allow_html=True)
        st.error(
            f"Cannot reach Ollama at `{ollama_url}`.\n\n"
            "**Fix:**\n"
            "```bash\n"
            "# Install Ollama from https://ollama.com\n"
            "ollama serve\n"
            f"ollama pull {model_input}\n"
            "```"
        )

    st.markdown("---")
    st.markdown("**Recommended free models**")
    st.markdown("""
| Model | Size | Notes |
|---|---|---|
| `mistral` | ~4 GB | Best quality |
| `llama3` | ~4 GB | Great reasoning |
| `llama3.2` | ~2 GB | Fast |
| `phi3` | ~2 GB | Lightweight |
| `gemma2` | ~5 GB | Google open |
""")

# Hero
st.markdown("""
<div class="hero">
    <h1>📄 Resume Parser</h1>
    <p>100% free &amp; local — powered by <b>Ollama</b>. No API keys, no cloud, no cost.</p>
</div>
""", unsafe_allow_html=True)

# Upload
col_up, _ = st.columns([2, 1])
with col_up:
    uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "docx"],
                                     help="Supported: PDF, DOCX")
    extract_btn = st.button("✨ Extract Resume Data")

# Process
if extract_btn:
    if uploaded_file is None:
        st.warning("Please upload a resume file first.")
    else:
        with st.spinner(f"Running Ollama ({model_input}) locally… this may take 20–60 s."):
            try:
                resp = requests.post(
                    f"{API_BASE}/api/upload",
                    files={"file": (uploaded_file.name,
                                    uploaded_file.getvalue(),
                                    uploaded_file.type)},
                    timeout=180,
                )
                if resp.status_code == 200:
                    st.session_state["result"] = resp.json()
                    st.success("Resume parsed successfully!")
                elif resp.status_code == 503:
                    st.error(
                        "**Ollama is not running.**\n\n"
                        "Start it with:\n```bash\nollama serve\n```\n"
                        f"Then pull your model:\n```bash\nollama pull {model_input}\n```"
                    )
                else:
                    detail = resp.json().get("detail", resp.text)
                    st.error(f"API Error {resp.status_code}: {detail}")
            except requests.exceptions.ConnectionError:
                st.error(
                    f"Cannot connect to the FastAPI backend at `{API_BASE}`.\n"
                    "Make sure it is running:\n```bash\nuvicorn app.main:app --reload\n```"
                )
            except Exception as e:
                st.error(f"Unexpected error: {e}")

# Results
if "result" in st.session_state:
    data   = st.session_state["result"]
    doc_id = data.get("document_id", "")
    resume = data.get("resume", {})

    st.markdown("---")
    st.markdown(f"**Document ID:** <span class='doc-id'>{doc_id}</span>",
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Contact
    with col1:
        contact = resume.get("contact", {})
        lines = []
        if contact.get("name"):     lines.append(f"<b>🙍 {contact['name']}</b>")
        if contact.get("email"):    lines.append(f"📧 {contact['email']}")
        if contact.get("mobile"):    lines.append(f"📞 {contact['mobile']}")
        if contact.get("location"): lines.append(f"📍 {contact['location']}")
        if contact.get("linkedin"): lines.append(f"🔗 <a href='{contact['linkedin']}' target='_blank'>LinkedIn</a>")
        if contact.get("github"):   lines.append(f"💻 <a href='{contact['github']}' target='_blank'>GitHub</a>")
        if contact.get("youtube"):   lines.append(f"📺 <a href='{contact['youtube']}' target='_blank'>YouTube</a>")
        if contact.get("website"):  lines.append(f"🌐 <a href='{contact['website']}' target='_blank'>Website</a>")
        body = "<br>".join(lines) if lines else "<i>No contact info found.</i>"
        st.markdown(f'<div class="card"><div class="card-header">👤 Contact Information</div>{body}</div>',
                    unsafe_allow_html=True)

    # Summary
    with col2:
        summary = resume.get("summary") or ""
        body = f"<p>{summary}</p>" if summary else "<i>No summary found.</i>"
        st.markdown(f'<div class="card"><div class="card-header">💼 Professional Summary</div>{body}</div>',
                    unsafe_allow_html=True)

    # Skills
    skills = resume.get("skills", {})
    skill_html = ""
    for label, key, css in [
        ("Technical",  "technical", ""),
        ("Languages",  "languages",  "badge-purple")
    ]:
        items = skills.get(key) or []
        if items:
            badges = " ".join(f"<span class='badge {css}'>{s}</span>" for s in items)
            skill_html += f"<p><b>{label}</b><br>{badges}</p>"
    if not skill_html:
        skill_html = "<i>No skills found.</i>"
    st.markdown(f'<div class="card"><div class="card-header">🛠️ Skills</div>{skill_html}</div>',
                unsafe_allow_html=True)

    # Work Experience
    work_exp = resume.get("work_experience") or []
    if work_exp:
        entries = ""
        for w in work_exp:
            resp_list = "".join(f"<li>{r}</li>" for r in (w.get("responsibilities") or []))
            resp_section = f"<ul style='margin:.4rem 0 0 0'>{resp_list}</ul>" if resp_list else ""
            loc = f" · {w['location']}" if w.get("location") else ""
            entries += f"""
            <div class="work-entry">
                <b>{w.get('role') or '—'}</b> @ {w.get('company') or '—'}
                <span style="color:#9ca3af;font-size:.85rem"> · {w.get('duration') or ''}{loc}</span>
                {resp_section}
            </div>"""
        st.markdown(f'<div class="card"><div class="card-header">💼 Work Experience</div>{entries}</div>',
                    unsafe_allow_html=True)

    # Education
    education = resume.get("education") or []
    if education:
        entries = ""
        for e in education:
            entries += f"""
            <div class="edu-entry">
                <b>{e.get('degree') or '—'}</b><br>
                {e.get('institution') or '—'}
                <span style="color:#9ca3af;font-size:.85rem"> · {e.get('year') or ''}</span>
            </div>"""
        st.markdown(f'<div class="card"><div class="card-header">🎓 Education</div>{entries}</div>',
                    unsafe_allow_html=True)

    # Certifications
    certs = resume.get("certifications") or []
    if certs:
        badges = " ".join(
            f"<span class='badge badge-orange'>🏅 {c.get('name') or 'Unknown'}"
            + (f" ({c['issuer']})" if c.get("issuer") else "")
            + (f" – {c['year']}" if c.get("year") else "")
            + "</span>"
            for c in certs
        )
        st.markdown(f'<div class="card"><div class="card-header">🏆 Certifications</div>{badges}</div>',
                    unsafe_allow_html=True)

    # Retrieve by ID
    with st.expander("🔍 Retrieve a previous result by Document ID"):
        lookup_id = st.text_input("Document ID", placeholder="Paste your document ID here")
        if st.button("Fetch"):
            if not lookup_id.strip():
                st.warning("Enter a document ID.")
            else:
                try:
                    r = requests.get(f"{API_BASE}/api/resume/{lookup_id.strip()}", timeout=30)
                    if r.status_code == 200:
                        st.json(r.json())
                    elif r.status_code == 404:
                        st.error("Document not found.")
                    else:
                        st.error(f"Error {r.status_code}: {r.json().get('detail', r.text)}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to the API.")