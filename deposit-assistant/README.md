# Deposit Dispute Assistant (Kuku AI Generalist Assignment)

An enterprise-grade **5-Layer Micro-RAG Legal Assistant** designed for ordinary tenants in India facing security deposit withholding. Built with Streamlit, Pydantic, and the official `google-genai` SDK (`gemini-3.5-flash-lite` & `text-embedding-004`).

Designed specifically to be **frictionless for evaluators**: runs instantly via `pip install -r requirements.txt` and `streamlit run app.py` without requiring external databases (no Docker, no PostgreSQL, no pgvector).

---

## 5-Layer Architecture

```
[ User Story (English / Hindi / Hinglish) ]
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  LAYER 1: Pre-Ingestion Guardrails & Fact Extraction   │
│  • Regex PII Redactor: Aadhaar, PAN, phone, email      │
│  • gemini-3.5-flash-lite: Tri-state Pydantic schema   │
│  • Dense Query Expander: Converts intake into legal Q  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  LAYER 2: Human-in-the-Loop Fact Confirmation          │
│  • Targeted follow-up loop (never repeats questions)   │
│  • UT & Location Normalizer (auto-resolves Delhi/UTs)  │
│  • Fact Lock: User verifies & locks state before RAG   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  LAYER 3: Frictionless In-Memory Vector Retrieval      │
│  • Verified Knowledge Base: statutes.json              │
│  • In-Memory NumPy Cosine Similarity Search            │
│  • text-embedding-004 (with offline BM25 fallback)     │
│  • Retrieves Top-2 relevant statutory clauses          │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  LAYER 4: Bounded Grounding & Statutory Synthesis      │
│  • Strictly bounded context prompt (<context> clauses) │
│  • Demand Notice Generator: Populates verified cites   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  LAYER 5: Post-Generation AST Citation Firewall        │
│  • Regex citation detector cross-referenced to context │
│  • Strips unverified/hallucinated sections in real time│
│  • Telemetry Dashboard: Latency, token costs, guardrail│
└────────────────────────────────────────────────────────┘
```

---

## Verified Knowledge Base (`statutes.json`)

The retrieval index contains verified statutory chunks from Indian laws:
1. **`ICA_SEC_73`**: Indian Contract Act, 1872 — Section 73 (Requirement of actual proven loss; normal wear and tear excepted).
2. **`MTA_SEC_11`**: Model Tenancy Act, 2021 — Section 11 (2-month security deposit limit and mandatory refund timeline).
3. **`MTA_SEC_15`**: Model Tenancy Act, 2021 — Section 15 (Division of maintenance duties; capital appliances vs. tenant routine care).
4. **`TPA_SEC_108`**: Transfer of Property Act, 1882 — Section 108(m) (Reasonable wear and tear excepted).
5. **`BSA_SEC_61`**: Bharatiya Sakshya Adhiniyam, 2023 — Section 61 (Admissibility of electronic records, UPI, WhatsApp).
6. **`RWA_BYLAWS`**: Model Cooperative Housing Society Bylaws — Bylaw 38 (Penalties require written show-cause and official receipts).

---

## Quickstart

### 1. Environment Setup

```powershell
# From the deposit-assistant directory
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure API Key (Optional)

Set your Gemini API key in the environment or paste it directly in the Streamlit sidebar:

```powershell
$env:GEMINI_API_KEY = "your-google-ai-studio-api-key"
$env:GEMINI_MODEL = "gemini-3.5-flash-lite"
```
*(If no API key is provided, the system seamlessly runs in local mock/fallback mode with offline BM25 retrieval).*

### 3. Run Automated Tests

```powershell
python -m unittest discover -v
```
*(Executes 58 comprehensive unit tests covering PII redaction, vector retrieval, citation firewall interception, UT mapping, demand notice generation, evidence strength scoring, pushback simulation, dispute resolution ROI, and court dossier compilation).*

### 4. Launch Streamlit Application

```powershell
streamlit run app.py
```
Open `http://localhost:8501` in your browser. Click sidebar preset **"Sample 1: Delhi (Business Losses)"** to observe the entire 5-layer pipeline in action.
