# KUKU AI GENERALIST ASSIGNMENT — PROBLEM 2: BUILD AN AI LAWYER
## Deposit Dispute Assistant: A 5-Layer Micro-RAG Legal Assistant for Indian Tenants

**Candidate:** Rudra Vohra | **Roll No:** 23113131 | **Branch:** Civil Engineering  
**GitHub Repository:** [github.com/R-V-7/Kuku_Assignment](https://github.com/R-V-7/Kuku_Assignment) | **Problem Selected:** Problem 2 (Build an AI Lawyer)  
**Deliverables:** Production Streamlit App, 58 Automated Unit Tests, 6 Raw Output Runs, 2-Page Solution Doc, Video Walkthrough  

---

### 1. Problem Choice, Framing & Scope
* **Why Security Deposit Disputes?** Over 70 million urban households in India rent their homes. Unlawful deposit retention is India's #1 urban consumer grievance. Landlords routinely withhold ₹20,000–₹1,00,000 under arbitrary pretexts (*"painting"*, *"deep cleaning"*, or *"business losses"*). With private advocate retainers costing ₹15,000–₹50,000, hiring a lawyer is financially irrational for claims under ₹1 Lakh. Tenants face a severe power asymmetry and surrender their hard-earned money out of intimidation.
* **Scope & Boundaries:**
  * **In-Scope:** Residential tenancies across all 28 Indian States and Union Territories (with automatic geographic normalization for UTs like Delhi and Chandigarh). Covers PII redaction, conversational fact extraction, dense query expansion, statutory vector retrieval, bounded legal evaluation, objective drafting (demand notice vs. mutual settlement), WhatsApp pushback rebuttals, litigation ROI analysis, and court complaint dossier compilation.
  * **Out-of-Scope (Explicit System Boundaries):** Commercial property leases, active court eviction proceedings, and criminal fraud/forgery (which require police FIRs and forensic investigation).
* **Assumptions Made:**
  1. *Evidentiary Reality:* Most urban tenants transfer deposits via UPI/NEFT, providing admissible electronic evidence under Section 61 of the Bharatiya Sakshya Adhiniyam, 2023 (BSA), even when written lease agreements are absent.
  2. *Statutory Wear & Tear:* Normal domestic wear and tear is the landlord's statutory maintenance duty; deductions require genuine third-party contractor GST invoices under Section 11 of the Model Tenancy Act, 2021 (MTA).
  3. *Tenant Privacy:* Indian tenants routinely share unredacted Aadhaar/PAN records; pre-LLM client-side PII masking is mandatory.

---

### 2. 5-Layer Micro-RAG Architecture & Division of Labor

To eliminate heavy infrastructure hurdles while guaranteeing zero hallucinations, we built a **zero-external-database Micro-RAG architecture** running entirely in-memory with NumPy cosine similarity:

| Architecture Layer | Handled by AI (`gemini-3.5-flash-lite`) | Handled by Deterministic Code & Rule-Based Guardrails |
| :--- | :--- | :--- |
| **Layer 1: Pre-Ingestion Guardrails & Fact Intake** | Conversational extraction of 9 factual fields from messy English/Hindi/Hinglish stories; dense query expansion. | **Regex PII Redactor:** Masks Aadhaar, PAN, phone numbers, and emails before API calls. Pydantic schema validation with tri-state logic (`yes`/`no`/`unknown`). |
| **Layer 2: Human-in-the-Loop Clarification Loop** | Dynamic parsing of user answers to targeted follow-up questions. | **Clarification State Machine:** Tracks missing fields and never asks the same question twice. **UT & City Resolver:** Auto-maps Delhi/Chandigarh and clears uncertainties. |
| **Layer 3: Frictionless In-Memory Vector RAG** | Vector embeddings via `text-embedding-004` (with offline BM25 fallback). | **In-Memory NumPy Store:** Cosine similarity search over verified `statutes.json` (ICA §73, MTA §11, BSA §61). Zero DB dependencies (no Postgres, pgvector, or Docker). |
| **Layer 4: Bounded Synthesis & Objective Routing** | Objective statutory summarization strictly bounded to retrieved `<context>` clauses; pushback roleplay. | **3-State Posture Machine:** Classifies case as *Unjustified* (demand notice), *Justified* (discharge record), or *Partial* (proportional demand) based on verified invoices. |
| **Layer 5: Post-Generation AST Citation Firewall** | *Zero trust granted to raw LLM generation.* | **AST Citation Firewall:** Scans text via regex, cross-references all citations against retrieval whitelist, strips unverified statutes, and logs telemetry. |

---

### 3. Product & AI Innovations (Beyond Generic Legal Chatbots)

1. **Evidence Strength & Win-Probability Meter (`evidence_meter.py`):** Computes a deterministic 0–100% case recovery score based on Indian evidence law: `+25%` for electronic bank trails (BSA 2023 §61), `+20%` for signed leases (ICA 1872 §10), and `+10%` for documented move-out dates (TPA §108). If the landlord fulfilled their statutory burden with valid GST invoices, the score recalibrates to **15% (Claim Unviable)**, actively warning tenants against futile litigation.
2. **Adversarial Landlord Pushback Simulator & WhatsApp Rebuttals (`simulator.py`):** Anticipates the 3 most common Indian landlord counter-arguments (*"Court takes 10 years"*, *"Notice period penalty forfeiture"*, and unproven repair charges) and equips the tenant with concise, copy-pasteable 2-line WhatsApp rebuttals citing MTA §11 60-day summary disposal, ICA §74 penalty bans, and DLSA Lok Adalat conciliation.
3. **Dispute Resolution Expected Value (EV) & Forum Advisor (`litigation_roi.py`):** Evaluates claim economics: for micro-claims (<₹15k), warns against private advocate retainers and recommends **₹0 Free DLSA Pre-Litigation Lok Adalat**; for mid-claims (₹15k–₹60k), recommends **e-Daakhil Consumer Commission** (₹0 court fees under ₹5 Lakhs); for claims >₹60k, calculates **accrued statutory interest (@ 8% p.a.)** under the *Interest Act, 1978* claimable before Rent Courts / Summary Civil Suits (Order 37 CPC).
4. **One-Click e-Daakhil / DLSA Court Dossier Compiler (`dossier.py`):** If the 15-day notice is ignored, one click compiles a complete, court-ready filing packet: Synopsis, Chronological List of Dates and Events, Statutory Grounds, Prayer for Relief, Verification, and an interactive Index of Annexures checklist.

---

### 4. Tools Used & Real-World Failure Analysis (Mandatory Brief Requirement)
* **AI Tools Used:** `gemini-3.5-flash-lite`, `text-embedding-004`, Claude, Google GenAI SDK, Streamlit.
* **Where the AI Got It Wrong (Real Run Failure Analysis):**  
  During testing of our Micro-RAG pipeline with `gemini-3.5-flash-lite`, the model committed a classic, dangerous legal AI hallucination: **it escalated a routine civil contract dispute into a criminal offense**, outputting:  
  > *"...withholding the deposit constitutes unjust enrichment and criminal breach of trust under Section 405 of the Indian Penal Code (IPC) / BNS."*  
  Even with context prompt constraints, `Section 405 IPC` was hallucinated from parametric memory (it did not exist in `statutes.json`). In Indian legal practice, framing a civil deposit dispute as criminal breach of trust is a fatal defect that courts dismiss with strictures.  
* **How Our Architecture Solved It:** This failure proved that prompt engineering alone is inadequate for legal reliability. We built the **Layer 5 AST Citation Firewall**:
  1. It parses output text for statutory citation patterns (`Section \d+`, `Article \d+`, `IPC`, `BNS`).
  2. It cross-references extracted citations against the whitelist of retrieved Layer 3 chunk IDs.
  3. Because `Section 405 IPC` was not in the whitelist, the firewall physically intercepted the unverified criminal charge, replaced it with verified civil remedies (**Section 73 Indian Contract Act**), and logged the interception in the Telemetry Dashboard.
* **The "Blind Advocate" & "Concession Hallucination" Failure:** Standard LLMs suffer from blind advocacy—conceding hallucinated bills when none were provided, or demanding 100% refunds when the landlord provided valid contractor GST invoices. We eliminated this by decoupling factual classification from drafting: our deterministic 3-state posture machine routes verified invoice cases to **Mutual Tenancy Discharge Records** and unproven retention cases to **Zero-Concession Demand Notices**.
* **Conversational Intake Failures Solved in Testing:**  
  1. *Substring Arithmetic Bug:* Naive checks like `'0' in reply` triggered on amounts containing zero (e.g. ₹15,000 or ₹40,000), resetting returned balances. We solved this with boundary-isolated regex tokens (`\b(0|zero|nil|none)\b`) and auto-deriving `max(0, deposit - deduction)`.  
  2. *Follow-Up Field Overwrites:* When tenants answered *"no agreement"* to follow-up questions, earlier iterations misattributed the negative answer, overwriting `state` or `city` with `"no"`. We built strict question-routing state machine guards that insulate geographic facts from document queries.  
  3. *The Bangalore "False Hope" Score:* Our initial Evidence Meter gave a tenant 70% confidence simply because they had bank records and a signed lease, despite the landlord producing verified contractor GST invoices for admitted damage. We recalibrated the engine so that MTA §11 invoice compliance gates the score to **15% (Unviable)**, preventing financially ruinous litigation.

---

### 5. Honest Failure Modes & When Someone Needs a Real Lawyer
1. **Counterfeit / Forged Landlord Invoices:** If a landlord produces fraudulent GST invoices or backdated repair slips, the assistant cannot conduct forensic handwriting or tax portal verification. The assistant explicitly flags this and instructs the tenant to file an affidavit before the District Consumer Commission.
2. **Cash Deposits & Oral Leases:** When both `written_agreement == "no"` and `payment_proof == "no"`, documentary proof under BSA Section 61 is absent. The system informs the user that civil claims require documentary custody proof; steers case to informal pre-litigation conciliation via DLSA Lok Adalat.
3. **Active Evictions & Physical Threats:** When disputes involve lockouts, disconnection of utilities, or physical intimidation, demand notices are insufficient. The app instructs the tenant to seek immediate police assistance and consult an advocate for interim civil injunctions.
4. **NRI Landlords & Informal Co-Living Aggregators:** In IT hubs (Bengaluru, Gurugram), properties are frequently owned by overseas NRIs or sub-leased through informal co-living startups. Standard Registered Post AD notice service fails without a domestic physical address. The system flags this jurisdiction hurdle and recommends serving notice via verified electronic channels (WhatsApp/email under BSA §61) alongside consumer forum e-filing.

---

### 6. Verification, Real-World Economics & Scalability
* **58 Automated Unit Tests (100% Pass Rate in <0.04s):** Ten test suites (`test_rag`, `test_engine`, `test_draft`, `test_guidance`, `test_followup`, `test_intake`, `test_evidence_meter`, `test_simulator`, `test_litigation_roi`, `test_dossier`) verify PII redaction, vector retrieval, citation firewall interception, UT auto-mapping, non-repeating follow-ups, evidence leverage scoring, pushback simulation, and court dossier compilation.
* **Real-World Economics & Sub-Second Latency:** Running in-memory NumPy vector retrieval requires zero database infrastructure (no Pinecone or pgvector bills). At ~1,200 tokens per interaction using `gemini-3.5-flash-lite` and `text-embedding-004`, end-to-end triage costs less than **$0.00015 USD (~₹0.012 INR)** per case. Processing 100,000 tenant disputes nationwide would cost only **$15 USD (~₹1,250 INR)**, proving that nationwide access to justice is viable at near-zero marginal cost.
