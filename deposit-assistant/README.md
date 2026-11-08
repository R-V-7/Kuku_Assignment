# Deposit Dispute Assistant (Kuku AI Generalist Assignment)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-red?logo=streamlit)](https://kukuassignment-83awbb7kp5dmr2vzfmafof.streamlit.app)
[![Tests](https://img.shields.io/badge/Unit%20Tests-58%20Passed-brightgreen)](SOLUTION_DOC.md)

> 🚀 **Live Interactive Web Prototype:**  
> **[kukuassignment-83awbb7kp5dmr2vzfmafof.streamlit.app](https://kukuassignment-83awbb7kp5dmr2vzfmafof.streamlit.app)**

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

## 💡 Key Product & AI Innovations

1. **📊 Evidence Strength & Win-Probability Meter (`evidence_meter.py`):** Calculates a dynamic 0–100% evidentiary recovery score based on Indian evidence law (BSA 2023 §61 electronic bank trails, ICA 1872 §10 written lease binding terms, and MTA 2021 §11 landlord expenditure burden). Accurately calibrates to 15% (Unviable) when landlords provide valid contractor GST invoices.
2. **🥊 Adversarial Landlord Pushback Simulator (`simulator.py`):** Predicts the 3 most common Indian landlord counter-arguments (*"Court takes 10 years"*, *"Notice period penalty forfeiture"*, and unproven repair charges) and equips the tenant with concise, copy-pasteable 2-line WhatsApp rebuttals citing MTA §11, Section 74 ICA, and DLSA Lok Adalat.
3. **⚖️ Dispute Resolution Expected Value (EV) & Forum Advisor (`litigation_roi.py`):** Calculates 8% p.a. accrued statutory interest under the *Interest Act, 1978*, warns against hiring private advocates for micro-claims (<₹15k), and guides users to ₹0 NALSA/DLSA Pre-Litigation Lok Adalats or self-filed e-Daakhil Consumer Commissions (zero court fees under ₹5 Lakh).
4. **📦 One-Click e-Daakhil / DLSA Court Dossier Compiler (`dossier.py`):** Generates a court-ready filing petition packet (.md) with a chronological List of Dates & Events, Statutory Grounds, Relief Prayer, and an interactive Index of Annexures checklist for immediate filing when notices are ignored.

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
