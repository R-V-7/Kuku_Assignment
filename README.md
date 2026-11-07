# Kuku AI Generalist Assignment — Problem 2: Deposit Dispute Assistant

[![Tests](https://img.shields.io/badge/Unit%20Tests-58%20Passed-brightgreen)](deposit-assistant/SOLUTION_DOC.md)
[![Architecture](https://img.shields.io/badge/Architecture-5--Layer%20Micro--RAG-blue)](deposit-assistant/SOLUTION_DOC.md)
[![Citation Firewall](https://img.shields.io/badge/Guardrails-AST%20Citation%20Firewall-orange)](deposit-assistant/SOLUTION_DOC.md)

An end-to-end, privacy-preserving, production-grade **Indian Residential Rental Security Deposit Triage & Formal Notice Engine** developed for the Kuku AI Generalist Assignment (Problem 2).

Built with a **zero-external-database Micro-RAG architecture** (`gemini-3.5-flash-lite`, in-memory vector cosine similarity, Pydantic tri-state validation, post-generation AST Citation Firewall, and evaluation-conditioned document drafting).

---

## 💡 Key Product & AI Innovations (Beyond Generic Legal Chatbots)

While most legal AI projects are simple "prompt-and-pray" demand letter generators, the **Deposit Dispute Assistant** introduces four substantive product innovations that transform it into an active, game-theoretic negotiation copilot:

### 1. 📊 Evidence Strength & Win-Probability Meter (`evidence_meter.py`)
* **What it does:** Computes a dynamic **0–100% Case Strength Score** grounded in the Indian statutory burden of proof.
* **Statutory Rigor:**
  * **+25% (BSA 2023 §61):** Electronic banking trail (UPI / NEFT records) serving as primary electronic evidence.
  * **+20% (ICA 1872 §10 & MTA 2021 §4):** Signed written lease agreement binding exit protocols.
  * **+10% (TPA 1882 §108(q)):** Documented move-out date establishing the statutory 30-day refund deadline.
  * **Objective Recalibration (MTA 2021 §11):** If the landlord complied with statutory requirements (provided genuine contractor GST invoices for admitted tenant damages), the score drops to **15% (Claim Unviable / Landlord Substantiated)**, actively warning the tenant against futile litigation.

### 2. 🥊 Adversarial Landlord Pushback Simulator & WhatsApp Rebuttals (`simulator.py`)
* **What it does:** Solves the real-world problem: *"What do I do 10 minutes after sending the demand notice when the landlord pushes back on WhatsApp?"*
* **Game-Theoretic Roleplay:** Simulates the 3 most common Indian landlord counter-strategies:
  1. *Procedural Intimidation:* *"Go to court, Indian courts take 10 years"* $\rightarrow$ Rebuttal cites MTA §11 summary 60-day Rent Authority disposal.
  2. *Notice Period Penalty Forfeiture:* *"You didn't give 2 months notice"* $\rightarrow$ Rebuttal cites ICA §74 penalty bans and TPA §106 15-day statutory baseline.
  3. *Unsubstantiated Expense Claims:* Custom excuses (*"business losses"*, *"broken geysers"*, *"deep cleaning"*) $\rightarrow$ Rebuttal cites MTA §11 GST invoice mandate.
* **Hybrid LLM Architecture:** Powered by `gemini-3.5-flash-lite` roleplay with an immediate, zero-latency deterministic fallback that interpolates any arbitrary dispute reason.

### 3. ⚖️ Dispute Resolution Expected Value (EV) & Forum Advisor (`litigation_roi.py`)
* **What it does:** Prevents financially self-destructive litigation by calculating the **Litigation ROI** across Indian forums:
  * **Micro-Claims (< ₹15,000):** Warns against hiring private advocates (lawyer retainers exceed claim value); recommends **₹0 Free Pre-Litigation Lok Adalat (NALSA/DLSA)** under the *Legal Services Authorities Act, 1987*.
  * **Mid-Range (₹15,000 – ₹60,000):** Recommends self-filing on **e-Daakhil (Consumer Commission)** with **₹0 Court Fee** (exempt for claims under ₹5 Lakh under CPA 2019).
  * **High-Value (> ₹60,000):** Recommends **Rent Authority / Summary Civil Suit (Order 37 CPC)** and computes **accrued statutory interest (@ 8.0% p.a.)** under the *Interest Act, 1978*.

### 4. 📦 One-Click e-Daakhil / DLSA Pre-Litigation Court Dossier (`dossier.py`)
* **What it does:** When landlords ignore the 15-day demand notice, tenants can generate a complete, court-ready filing petition packet in one click:
  1. **Court Heading & Jurisdiction:** Formatted for District Consumer Commissions or DLSA Lok Adalat.
  2. **Chronological List of Dates and Events:** Auto-formatted timeline mapping facts to statutory provisions.
  3. **Statutory Grounds:** Grounded in ICA §73/74, MTA §11, and BSA §61.
  4. **Prayer & Relief:** Principal refund + statutory interest + nominal litigation compensation.
  5. **Verification & Index of Annexures:** Interactive checklist (Lease agreement, Bank proof, Key handover confirmation, Postal tracking).
  6. **Objective Discharge Mode:** In justified cases, automatically compiles an Accord & Satisfaction Tenancy Discharge Dossier (ICA §63) instead of an adversarial complaint.

---

## 📁 Repository Structure

```
.
├── Kuku — AI Generalist Assignment (1).pdf # Problem statement & specifications
└── deposit-assistant/                      # Complete production Streamlit application
    ├── app.py                              # 5-Layer Streamlit interactive interface
    ├── engine.py                           # High-level orchestrator for the 5-layer pipeline
    ├── models.py                           # Pydantic schema, UT/state resolvers, tri-state logic
    ├── intake.py                           # Conversational fact extraction via Gemini 3.5 Flash Lite
    ├── followup.py                         # Deterministic clarification state machine
    ├── guidance.py                         # Evaluation-conditioned legal guidance engine
    ├── draft.py                            # Strict 3-state legal drafting machine (Notice vs. Settlement)
    ├── drafter.py                          # Alias module for draft.py
    ├── evidence_meter.py                   # Evidence Strength & Win-Probability Meter (BSA §61 & ICA §10)
    ├── simulator.py                        # Landlord Pushback Simulator & WhatsApp Rebuttals
    ├── litigation_roi.py                   # Dispute Resolution EV & Forum Advisor (NALSA/e-Daakhil)
    ├── dossier.py                          # One-Click Court Dossier & Complaint Petition Compiler
    ├── statutes.json                       # Verified Indian statutory knowledge base
    ├── rag/                                # Micro-RAG pipeline
    │   ├── redactor.py                     # Layer 1: PII Redaction (Aadhaar, PAN, phone)
    │   ├── expander.py                     # Layer 1: Dense statutory query expander
    │   ├── store.py                        # Layer 3: In-memory vector store (numpy cosine similarity)
    │   ├── generator.py                    # Layer 4: Bounded statutory synthesis
    │   └── firewall.py                     # Layer 5: AST Citation Firewall (anti-hallucination)
    ├── raw_outputs/                        # 6 unedited case outputs (JSON + legal notices)
    ├── SOLUTION_DOC.md                     # Comprehensive 2-page system architecture documentation
    ├── WALKTHROUGH_SCRIPT.md               # 2-minute Loom/video demonstration script
    └── test_*.py                           # 58 automated unit tests across 10 test suites
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
* Python 3.10+
* (Optional) `GEMINI_API_KEY` for live LLM extraction & vector embeddings (the app includes full offline mock fallbacks if no key is supplied).

### 2. Installation
```bash
cd deposit-assistant
python -m venv .venv

# Windows:
.\.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Launching the Application
```bash
streamlit run app.py
```

### 4. Running the Test Suite (58 Unit Tests)
```bash
python -m unittest discover -v
```

---

## 🛡️ 5-Layer Micro-RAG Architecture

1. **Layer 1: Pre-Ingestion Guardrails & Fact Intake**
   - Regex masking for Aadhaar (`\d{4}\s\d{4}\s\d{4}`), PAN (`[A-Z]{5}\d{4}[A-Z]`), and Indian mobile numbers (`(?:\+91)?[6-9]\d{9}`).
   - Structured JSON schema enforcement with strict Pydantic tri-state validation (`"yes"`, `"no"`, `"unknown"`).
   - Dynamic deduction reasons (supports arbitrary reasons like "business losses" without rigid Enum constraints).
   - Auto-mapping for all 28 Indian States, Union Territories (Delhi, Chandigarh), and major rental hubs.

2. **Layer 2: Human-in-the-Loop Clarification Loop**
   - Deterministic state machine asking only targeted, non-repeating follow-up questions for missing facts.
   - Automatic derivation of returned amount when deposit and deduction are known.

3. **Layer 3: Zero-External-DB Micro-RAG Retrieval**
   - Pure in-memory vector store using NumPy cosine similarity over verified statutory text (`statutes.json`).
   - Retrieves top-$k$ statutory clauses from the **Indian Contract Act, 1872 (Section 73)**, **Model Tenancy Act, 2021 (Section 11)**, and **Bharatiya Sakshya Adhiniyam, 2023 (Section 61)**.

4. **Layer 4: Bounded Statutory Synthesis & Objective Legal Posture**
   - Strictly bounded prompts preventing ungrounded legal conclusions.
   - **3-State Dispute Routing**:
     - *Unjustified (0% Proven)*: 15-day formal demand notice for 100% refund; zero concession language.
     - *Justified (100% Proven)*: Formal Tenancy Settlement & Discharge Record; advises against futile litigation.
     - *Partially Justified (Mixed Evidence)*: Partial refund demand conceding only specifically verified expenses.

5. **Layer 5: Post-Generation AST Citation Firewall & Telemetry**
   - Inspects generated text citations against the whitelist of retrieved chunks.
   - Intercepts and replaces ungrounded citations (e.g. criminal escalation under Section 405 IPC) with verified civil remedies before display.

