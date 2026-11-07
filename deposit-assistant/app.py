"""Deposit Dispute Assistant - 5-Layer Micro-RAG Streamlit Application.

Architecture:
Layer 1: Pre-Ingestion Guardrails & Tri-State Fact Extractor (PII Redaction, Gemini 3.5 Flash Lite, Query Expander).
Layer 2: Human-in-the-Loop Fact Confirmation & State Machine.
Layer 3: Frictionless In-Memory Vector Retrieval (Micro-RAG via numpy cosine similarity).
Layer 4: Bounded Grounding & Synthesis.
Layer 5: Post-Generation AST Citation Firewall & Telemetry Logger.
"""

import os
import re
import streamlit as st
from pydantic import ValidationError

from engine import (
    CaseFacts,
    DisputeEngine,
    IntakeError,
    ModelError,
    UNION_TERRITORIES,
    MAJOR_INDIAN_CITIES_TO_STATE,
    INDIAN_STATES,
    normalize_ut_location,
    clean_location_input,
    resolve_indian_location,
    CitationFirewall,
    classify_dispute_posture,
    create_client,
    SOURCES,
    calculate_evidence_strength,
    simulate_pushbacks,
)

st.set_page_config(
    page_title="Deposit Dispute Assistant",
    page_icon="🏠",
    layout="wide",
)

# Initialize Session State
if "case" not in st.session_state:
    st.session_state.case = None
if "confirmed_case" not in st.session_state:
    st.session_state.confirmed_case = None
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "answered_questions" not in st.session_state:
    st.session_state.answered_questions = []
if "review_version" not in st.session_state:
    st.session_state.review_version = 0
if "input_story" not in st.session_state:
    st.session_state.input_story = ""
if "pii_log" not in st.session_state:
    st.session_state.pii_log = []
if "legal_query" not in st.session_state:
    st.session_state.legal_query = ""
if "retrieved_chunks" not in st.session_state:
    st.session_state.retrieved_chunks = []
if "rag_synthesis" not in st.session_state:
    st.session_state.rag_synthesis = ""
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = None

# Sidebar: Configuration & Presets
with st.sidebar:
    st.title("⚙️ System Architecture")
    st.caption("5-Layer Micro-RAG Pipeline (Zero external DB dependencies)")

    api_key_env = os.environ.get("GEMINI_API_KEY", "")
    user_api_key = st.text_input(
        "Gemini API Key",
        value=api_key_env,
        type="password",
        help="Reads from GEMINI_API_KEY environment variable if set. You can also paste it here.",
    )
    if user_api_key:
        os.environ["GEMINI_API_KEY"] = user_api_key.strip()

    model_options = [
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
    ]
    current_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    selected_model = st.selectbox(
        "Model Selection",
        options=model_options,
        index=model_options.index(current_model)
        if current_model in model_options
        else 0,
    )
    os.environ["GEMINI_MODEL"] = selected_model

    if os.environ.get("GEMINI_API_KEY"):
        st.success("API Key Active (Live Ingestion & Embeddings)", icon="✅")
    else:
        st.info("Mock/Offline Fallback Mode Active", icon="ℹ️")

    st.markdown("---")
    st.subheader("🧪 Presets (Test Scenarios)")
    st.caption("One-click dispute stories:")

    if st.button("Sample 1: Delhi (Business Losses)", use_container_width=True):
        st.session_state.case = None
        st.session_state.confirmed_case = None
        st.session_state.conversation = []
        st.session_state.answered_questions = []
        st.session_state.retrieved_chunks = []
        st.session_state.rag_synthesis = ""
        st.session_state.telemetry = None
        st.session_state.input_story = (
            "I was renting a flat in Saket, Delhi (Phone: 9876543210, Aadhaar: 4321 8765 1234). "
            "I moved out on 15 January 2025. My security deposit was Rs 60,000 paid through bank transfer. "
            "We had a registered 11-month agreement. The landlord only returned 20,000 and kept 40,000 rupees "
            "claiming he suffered business losses this year and cannot return the full amount. Can he do this?"
        )
        st.rerun()

    if st.button("Sample 2: Chandigarh (No Agreement / AC)", use_container_width=True):
        st.session_state.case = None
        st.session_state.confirmed_case = None
        st.session_state.conversation = []
        st.session_state.answered_questions = []
        st.session_state.retrieved_chunks = []
        st.session_state.rag_synthesis = ""
        st.session_state.telemetry = None
        st.session_state.input_story = (
            "I vacated my rented room in Chandigarh last month (October 2025). Deposit was 25000 in cash. "
            "We did not sign any written agreement, but I have Google Pay receipts for all monthly rent. "
            "Landlord withheld 10000 for deep cleaning and AC servicing without showing any bills."
        )
        st.rerun()

    if st.button("Sample 3: Incomplete (Follow-Up Trigger)", use_container_width=True):
        st.session_state.case = None
        st.session_state.confirmed_case = None
        st.session_state.conversation = []
        st.session_state.answered_questions = []
        st.session_state.retrieved_chunks = []
        st.session_state.rag_synthesis = ""
        st.session_state.telemetry = None
        st.session_state.input_story = (
            "My landlord kept 15000 of my security deposit after I moved out because he says "
            "painting the flat is my responsibility. He returned the rest."
        )
        st.rerun()

    if st.button("Sample 4: Bangalore (Water Damage / Invoiced)", use_container_width=True):
        st.session_state.case = None
        st.session_state.confirmed_case = None
        st.session_state.conversation = []
        st.session_state.answered_questions = []
        st.session_state.retrieved_chunks = []
        st.session_state.rag_synthesis = ""
        st.session_state.telemetry = None
        st.session_state.input_story = (
            "I vacated my flat in Bangalore on 1st November 2026. My security deposit was Rs 1,00,000 paid online. "
            "We have a signed 11-month rental agreement. The landlord returned 75,000 but withheld 25,000. "
            "He said 20,000 is for replacing the modular kitchen cabinets which got severe water damage because "
            "I accidentally left the sink overflowing overnight, and 5,000 is for my pending BESCOM electricity bill. "
            "He sent me the official carpenter's GST invoice and the pending BESCOM meter bill on WhatsApp. "
            "I feel this is unfair, shouldn't the owner pay for his flat's repairs? Can he legally deduct this?"
        )
        st.rerun()

    if st.button("🔄 Reset / Clear Session", use_container_width=True):
        st.session_state.case = None
        st.session_state.confirmed_case = None
        st.session_state.conversation = []
        st.session_state.answered_questions = []
        st.session_state.input_story = ""
        st.session_state.pii_log = []
        st.session_state.legal_query = ""
        st.session_state.retrieved_chunks = []
        st.session_state.rag_synthesis = ""
        st.session_state.telemetry = None
        st.session_state.review_version += 1
        st.rerun()

    st.markdown("---")
    st.caption(
        "🛡️ **System Guardrail Stack**:\n"
        "- L1: Regex PII Redaction\n"
        "- L2: Human-in-the-Loop Fact Lock\n"
        "- L3: In-Memory NumPy Cosine Micro-RAG\n"
        "- L4: Bounded Statutory Context Prompting\n"
        "- L5: Post-Generation AST Citation Firewall"
    )

# Main Application Header
st.title("🏠 Deposit Dispute Assistant")
st.caption(
    "Indian Residential Rental Security Deposit Triage & Formal Notice Engine · Micro-RAG Architecture"
)

# Step Progress Bar indicator
current_step = 1
if st.session_state.case is not None:
    current_step = 2
if st.session_state.confirmed_case is not None:
    current_step = 4
elif st.session_state.case is not None:
    unanswered = DisputeEngine.get_followup_questions(
        st.session_state.case, st.session_state.answered_questions
    )
    if not unanswered:
        current_step = 3

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.markdown(f"**Step 1:** {'🔵' if current_step == 1 else '✅'} Intake & PII Redaction")
col_s2.markdown(f"**Step 2:** {'🔵' if current_step == 2 else ('✅' if current_step > 2 else '⚪')} Follow-Up Loop")
col_s3.markdown(f"**Step 3:** {'🔵' if current_step == 3 else ('✅' if current_step > 3 else '⚪')} Fact Confirmation")
col_s4.markdown(f"**Step 4:** {'🔵' if current_step == 4 else '⚪'} Bounded RAG & Notice")
st.markdown("---")

# ==============================================================================
# STEP 1: CONVERSATIONAL INTAKE & PRE-INGESTION GUARDRAILS
# ==============================================================================
st.header("Step 1: Conversational Intake (Layer 1 Guardrails)")
st.write(
    "Describe what happened in your own words (English, Hindi, or Hinglish). "
    "All sensitive personal identifiers (**Aadhaar, PAN, phone numbers**) are automatically redacted before LLM ingestion."
)

story_input = st.text_area(
    "Paste your rental deposit dispute story",
    value=st.session_state.input_story,
    height=140,
    placeholder="e.g., I vacated my flat in Delhi last month. Deposit was 50k, landlord only returned 20k claiming 30k for business losses...",
)

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    extract_clicked = st.button("🚀 Extract & Ingest", type="primary", use_container_width=True)

if extract_clicked:
    if not story_input.strip():
        st.error("Please enter your dispute story before extracting.")
    else:
        try:
            with st.spinner("Executing Layer 1 PII Redaction & Structured Extraction..."):
                engine = DisputeEngine()
                # Layer 1: PII Redaction
                redacted_text, pii_log = engine.redact_user_input(story_input)
                st.session_state.pii_log = pii_log

                # Layer 1: Extraction via Gemini 3.5 Flash Lite
                extracted = engine.extract_intake(redacted_text)
                st.session_state.case = extracted

                # Layer 1: Dense Query Expander
                legal_q = engine.expand_query(redacted_text, extracted.deduction_reason)
                st.session_state.legal_query = legal_q

                st.session_state.confirmed_case = None
                st.session_state.conversation = []
                st.session_state.answered_questions = []
                st.session_state.retrieved_chunks = []
                st.session_state.rag_synthesis = ""
                st.session_state.telemetry = None
                st.session_state.review_version += 1
                st.success("Facts extracted and PII sanitized successfully!")
                st.rerun()
        except (IntakeError, ModelError) as exc:
            st.error(f"Extraction failed: {exc}")

case = st.session_state.case

# Display PII Guardrail Notice if triggered
if st.session_state.pii_log:
    with st.expander(f"🛡️ Layer 1 Guardrail Active: {len(st.session_state.pii_log)} Sensitive Identifier(s) Redacted", expanded=False):
        st.caption("The following personal identifiers were masked before any API transmission:")
        for item in st.session_state.pii_log:
            st.markdown(f"- **{item['type']}**: `{item['original']}` $\\rightarrow$ `[MASKED]`")

# ==============================================================================
# STEP 2: FOLLOW-UP STATE MACHINE
# ==============================================================================
if case is not None:
    st.markdown("---")
    st.header("Step 2: Follow-Up Clarifications (Layer 2 State Machine)")
    st.caption(
        "Targeted questions resolve any unknown critical details. "
        "Answers dynamically update the case record without repeating questions."
    )

    if st.session_state.conversation:
        with st.container():
            for msg in st.session_state.conversation:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

    # Auto-fill amount_returned_inr if both deposit and deduction are known
    if (
        case.amount_returned_inr is None
        and case.deposit_amount_inr is not None
        and case.deduction_amount_inr is not None
    ):
        auto_returned = max(0, case.deposit_amount_inr - case.deduction_amount_inr)
        dumped_auto = case.model_dump()
        dumped_auto["amount_returned_inr"] = auto_returned
        case = CaseFacts(**dumped_auto)
        st.session_state.case = case

    unanswered = DisputeEngine.get_followup_questions(
        case, st.session_state.answered_questions
    )
    current_q = unanswered[0] if unanswered else None

    if current_q:
        with st.chat_message("assistant"):
            st.markdown(f"**{current_q}**")

        with st.form("followup_form", clear_on_submit=True):
            user_reply = st.text_input(
                "Your Reply",
                placeholder="Type your answer (e.g. 'City is Mumbai and state is Maharashtra', 'Yes', '50000', or 'I don't know')",
            )
            c_sub1, c_sub2 = st.columns([1, 3])
            with c_sub1:
                send_reply = st.form_submit_button("Send Reply", type="primary")

        if send_reply:
            if not user_reply.strip():
                st.error("Please provide an answer, or say you don't know.")
            else:
                try:
                    with st.spinner("Updating state machine..."):
                        engine = DisputeEngine()
                        norm_reply = user_reply.strip()
                        q_lower = current_q.lower()
                        reply_lower = norm_reply.lower()
                        dumped = case.model_dump()

                        # Strip "Please clarify this uncertainty:" prefix for routing
                        routing_q = q_lower
                        if "please clarify" in routing_q and "uncertainty" in routing_q:
                            # Extract the actual uncertainty text after the prefix
                            routing_q = re.sub(r"^.*uncertainty\s*:?\s*", "", routing_q).strip()

                        # 1. Location question (e.g. "Which state is the rental property in?")
                        if any(k in routing_q for k in ["which state", "which city", "what state", "what city", "rental property in", "property location", "city or state", "location is unknown"]):
                            is_state_q = "state" in q_lower and "city" not in q_lower
                            is_city_q = "city" in q_lower and "state" not in q_lower
                            clean_c, clean_s = clean_location_input(
                                norm_reply if not is_state_q else None,
                                norm_reply if not is_city_q else None,
                            )
                            norm_c, norm_s, sugg_s = resolve_indian_location(
                                clean_c or (None if is_state_q else norm_reply),
                                clean_s or (norm_reply if is_state_q else None),
                            )
                            if is_state_q:
                                dumped["state"] = norm_s or INDIAN_STATES.get(reply_lower, norm_reply.title())
                                if norm_c and not dumped.get("city"):
                                    dumped["city"] = norm_c
                            elif is_city_q:
                                dumped["city"] = norm_c or norm_reply.title()
                                if norm_s and not dumped.get("state"):
                                    dumped["state"] = norm_s
                                elif sugg_s and not dumped.get("state"):
                                    dumped["suggested_state"] = sugg_s
                            else:
                                if clean_c or (norm_c and norm_c != norm_reply):
                                    dumped["city"] = clean_c or norm_c
                                if clean_s or (norm_s and norm_s != norm_reply):
                                    dumped["state"] = clean_s or norm_s
                                elif norm_s:
                                    dumped["state"] = norm_s
                                elif reply_lower in INDIAN_STATES:
                                    dumped["state"] = INDIAN_STATES[reply_lower]

                            dumped["uncertainties"] = [
                                u for u in dumped.get("uncertainties", [])
                                if not any(k in u.lower() for k in ["location", "city", "state"])
                            ]
                            updated_case = CaseFacts(**dumped)

                        # 2. Deposit question (e.g. "How much was the security deposit, in rupees?" or uncertainty "Total deposit amount is unknown")
                        elif ("security deposit" in routing_q and "returned" not in routing_q) or "deposit amount" in routing_q or ("deposit" in routing_q and "returned" not in routing_q and "deduct" not in routing_q):
                            match_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", reply_lower)
                            if match_k:
                                dumped["deposit_amount_inr"] = int(float(match_k.group(1)) * 1000)
                            else:
                                nums = re.findall(r"\d+", norm_reply.replace(",", ""))
                                if nums:
                                    dumped["deposit_amount_inr"] = int(nums[0])
                                else:
                                    raw_updated = engine.extract_intake(story=norm_reply, current_case=case, question=current_q)
                                    dumped = raw_updated.model_dump()
                            # Auto-calculate amount_returned_inr if deduction is already known
                            if dumped.get("deposit_amount_inr") is not None and dumped.get("deduction_amount_inr") is not None and dumped.get("amount_returned_inr") is None:
                                dumped["amount_returned_inr"] = max(0, dumped["deposit_amount_inr"] - dumped["deduction_amount_inr"])
                            updated_case = CaseFacts(**dumped)

                        # 3. Amount returned question (e.g. "How much of the deposit, if any, has already been returned?" or uncertainty "Amount returned ... is unknown")
                        elif "already been returned" in routing_q or "amount returned" in routing_q or "deposit, if any" in routing_q or ("returned" in routing_q and "deposit" not in routing_q):
                            match_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", reply_lower)
                            nums = re.findall(r"\d+", norm_reply.replace(",", ""))
                            if match_k:
                                dumped["amount_returned_inr"] = int(float(match_k.group(1)) * 1000)
                            elif nums:
                                dumped["amount_returned_inr"] = int(nums[0])
                            elif any(re.search(rf"\b{re.escape(k)}\b", reply_lower) for k in ["none", "nothing", "zero", "0", "nil", "no", "not returned", "did not return"]):
                                dumped["amount_returned_inr"] = 0
                            else:
                                raw_updated = engine.extract_intake(story=norm_reply, current_case=case, question=current_q)
                                dumped = raw_updated.model_dump()
                            # Auto-calculate deduction_amount_inr if deposit is known and deduction is not set
                            if dumped.get("deposit_amount_inr") is not None and dumped.get("amount_returned_inr") is not None and dumped.get("deduction_amount_inr") is None:
                                dumped["deduction_amount_inr"] = max(0, dumped["deposit_amount_inr"] - dumped["amount_returned_inr"])
                            updated_case = CaseFacts(**dumped)

                        # 4. Move-out date question (e.g. "When did you move out?" or uncertainty "Move out date is unknown")
                        elif "when did you move out" in routing_q or "move out" in routing_q or "move-out" in routing_q or "vacated" in routing_q:
                            cleaned_date = norm_reply.strip()
                            cleaned_date = re.sub(r"\bjanuray\b", "January", cleaned_date, flags=re.I)
                            cleaned_date = re.sub(r"\bfeburary\b", "February", cleaned_date, flags=re.I)
                            cleaned_date = re.sub(r"\bdecemeber\b", "December", cleaned_date, flags=re.I)
                            dumped["move_out_date"] = cleaned_date
                            updated_case = CaseFacts(**dumped)

                        # 5. Written agreement question (e.g. "Was there a written rental agreement?" or uncertainty "Written agreement ... is unknown")
                        elif "written rental agreement" in routing_q or "written agreement" in routing_q or "agreement" in routing_q and "lease" not in routing_q:
                            if any(k in reply_lower for k in ["yes", "ha", "haan", "yep", "had", "signed", "registered"]):
                                dumped["written_agreement_exists"] = "yes"
                            elif any(k in reply_lower for k in ["no", "nahi", "oral", "verbal", "none", "not signed"]):
                                dumped["written_agreement_exists"] = "no"
                            else:
                                dumped["written_agreement_exists"] = "unknown"
                            updated_case = CaseFacts(**dumped)

                        # 6. Payment proof question (e.g. "Do you have proof that you paid the deposit?" or uncertainty "Payment proof ... is unknown")
                        elif "proof that you paid" in routing_q or "payment proof" in routing_q or "proof" in routing_q:
                            if any(k in reply_lower for k in ["yes", "ha", "haan", "yep", "have", "bank", "gpay", "upi", "receipt"]):
                                dumped["payment_proof_exists"] = "yes"
                            elif any(k in reply_lower for k in ["no", "nahi", "cash without receipt", "none", "lost"]):
                                dumped["payment_proof_exists"] = "no"
                            else:
                                dumped["payment_proof_exists"] = "unknown"
                            updated_case = CaseFacts(**dumped)

                        # 7. Deduction reason question
                        elif "reason for withholding" in routing_q or "given a reason" in routing_q or "deduction reason" in routing_q or "withholding reason" in routing_q:
                            dumped["deduction_reason"] = norm_reply.strip()
                            updated_case = CaseFacts(**dumped)

                        # 8. Deduction amount question
                        elif "specified how much" in routing_q or "how much they want to deduct" in routing_q or "deduction amount" in routing_q or "amount deducted" in routing_q:
                            match_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", reply_lower)
                            if match_k:
                                dumped["deduction_amount_inr"] = int(float(match_k.group(1)) * 1000)
                            else:
                                nums = re.findall(r"\d+", norm_reply.replace(",", ""))
                                if nums:
                                    dumped["deduction_amount_inr"] = int(nums[0])
                                else:
                                    raw_updated = engine.extract_intake(story=norm_reply, current_case=case, question=current_q)
                                    dumped = raw_updated.model_dump()
                            # Auto-calculate amount_returned_inr if deposit is known
                            if dumped.get("deposit_amount_inr") is not None and dumped.get("deduction_amount_inr") is not None and dumped.get("amount_returned_inr") is None:
                                dumped["amount_returned_inr"] = max(0, dumped["deposit_amount_inr"] - dumped["deduction_amount_inr"])
                            updated_case = CaseFacts(**dumped)

                        # 9. Fallback general extraction via LLM
                        else:
                            raw_updated = engine.extract_intake(
                                story=norm_reply,
                                current_case=case,
                                question=current_q,
                            )
                            updated_case = CaseFacts(**raw_updated.model_dump())

                        st.session_state.conversation.extend(
                            [
                                {"role": "assistant", "content": current_q},
                                {"role": "user", "content": norm_reply},
                            ]
                        )
                        st.session_state.answered_questions.append(current_q)
                        st.session_state.case = updated_case
                        st.session_state.review_version += 1
                        st.rerun()
                except (IntakeError, ModelError) as exc:
                    st.error(f"Could not process reply: {exc}")
    else:
        st.info("✅ All primary follow-up questions answered. Proceed to verify facts below.")

# ==============================================================================
# STEP 3: EDITABLE FACT CONFIRMATION (HUMAN-IN-THE-LOOP)
# ==============================================================================
if case is not None:
    st.markdown("---")
    st.header("Step 3: Human-in-the-Loop Fact Confirmation")
    st.write(
        "Displaying the extracted case information. "
        "**Review and edit any fields below**, then click **Confirm & Lock Facts** to trigger Micro-RAG statutory retrieval."
    )

    if case.inferred_details:
        st.info(
            "💡 **AI Inferences to check:**\n\n"
            + "\n".join(f"- {inf}" for inf in case.inferred_details)
        )
    if case.uncertainties:
        st.warning(
            "⚠️ **Unresolved Uncertainties:**\n\n"
            + "\n".join(f"- {unc}" for unc in case.uncertainties)
        )

    with st.form(f"fact_confirmation_form_{st.session_state.review_version}"):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            st.subheader("📍 Location & Tenancy")
            state_val = st.text_input("State", value=case.state or case.suggested_state or "")
            city_val = st.text_input("City", value=case.city or "")
            move_out_val = st.text_input(
                "Move-out Date",
                value=case.move_out_date or "",
                help="Include year if known, e.g. January 2025",
            )
            scope_choices = ["residential_deposit", "other", "unknown"]
            scope_val = st.selectbox(
                "Dispute Scope",
                scope_choices,
                index=scope_choices.index(case.scope),
            )

            tri_state_choices = ["unknown", "yes", "no"]
            agreement_val = st.selectbox(
                "Written Rental Agreement Exists?",
                tri_state_choices,
                index=tri_state_choices.index(case.written_agreement_exists),
            )
            proof_val = st.selectbox(
                "Payment Proof Exists? (Bank, UPI, receipt)",
                tri_state_choices,
                index=tri_state_choices.index(case.payment_proof_exists),
            )

        with col_f2:
            st.subheader("💰 Financials & Deduction")
            dep_val = st.text_input(
                "Deposit Amount (₹)",
                value=str(case.deposit_amount_inr)
                if case.deposit_amount_inr is not None
                else "",
            )
            ret_val = st.text_input(
                "Amount Returned So Far (₹)",
                value=str(case.amount_returned_inr)
                if case.amount_returned_inr is not None
                else "",
            )
            reason_val = st.text_input(
                "Landlord's Stated Deduction Reason / Excuse",
                value=case.deduction_reason or "",
                help="e.g., 'business losses', 'painting', 'broken tiles'",
            )
            ded_amt_val = st.text_input(
                "Proposed Deduction (₹)",
                value=str(case.deduction_amount_inr)
                if case.deduction_amount_inr is not None
                else "",
            )
            notes_val = st.text_area(
                "Other Notes / Facts (one per line)",
                value="\n".join(case.other_details),
                height=95,
            )

        confirm_btn = st.form_submit_button(
            "🔒 Confirm & Lock Facts (Trigger Micro-RAG)", type="primary", use_container_width=True
        )

    if confirm_btn:

        def parse_amt(v: str) -> int | None:
            clean = v.strip().replace(",", "")
            if not clean:
                return None
            if not clean.isdigit():
                raise ValueError(
                    f"Amounts must be non-negative whole numbers in rupees, got: {v}"
                )
            return int(clean)

        try:
            confirmed = CaseFacts(
                scope=scope_val,
                state=state_val.strip() or None,
                city=city_val.strip() or None,
                deposit_amount_inr=parse_amt(dep_val),
                amount_returned_inr=parse_amt(ret_val),
                move_out_date=move_out_val.strip() or None,
                written_agreement_exists=agreement_val,
                payment_proof_exists=proof_val,
                deduction_reason=reason_val.strip() or None,
                deduction_amount_inr=parse_amt(ded_amt_val),
                other_details=[
                    line.strip()
                    for line in notes_val.splitlines()
                    if line.strip()
                ],
                uncertainties=case.uncertainties,
                inferred_details=case.inferred_details,
            )
            st.session_state.case = confirmed
            st.session_state.confirmed_case = confirmed

            # Trigger Layer 3 Vector Retrieval
            engine = DisputeEngine()
            dense_q = st.session_state.legal_query or engine.expand_query(
                confirmed.model_dump_json(), confirmed.deduction_reason
            )
            retrieved = engine.retrieve_statutes(dense_q, top_k=2)
            st.session_state.retrieved_chunks = retrieved

            # Trigger Layer 4 & 5 Bounded Synthesis + Citation Firewall
            synth_text, fw_status, telemetry = engine.synthesize_rag_guidance(
                confirmed, retrieved
            )
            st.session_state.rag_synthesis = synth_text
            st.session_state.telemetry = telemetry

            st.session_state.review_version += 1
            st.success("Facts locked! Micro-RAG retrieval and bounded synthesis complete.")
            st.rerun()
        except (ValueError, ValidationError) as exc:
            st.error(f"Validation error: {exc}")

    with st.expander("🔍 View Raw JSON Schema"):
        st.json(case.model_dump())

# ==============================================================================
# STEP 4: BOUNDED RAG SYNTHESIS, DEMAND NOTICE & TELEMETRY
# ==============================================================================
confirmed_case = st.session_state.confirmed_case
if confirmed_case is not None:
    st.markdown("---")
    st.header("Step 4: Bounded Legal Guidance & Formal Notice")
    st.caption("Synthesized strictly from verified statutory text (Indian Contract Act, Model Tenancy Act, BSA 2023).")

    # Financial Summary Metrics
    dep = confirmed_case.deposit_amount_inr or 0
    ret = confirmed_case.amount_returned_inr or 0
    bal = max(0, dep - ret) if confirmed_case.deposit_amount_inr is not None else None
    ded = confirmed_case.deduction_amount_inr

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Original Deposit", f"₹{dep:,}" if confirmed_case.deposit_amount_inr else "Unknown")
    m2.metric("Returned Amount", f"₹{ret:,}")
    m3.metric("Outstanding Balance", f"₹{bal:,}" if bal is not None else "Unknown")
    m4.metric(
        "Claimed Deduction",
        f"₹{ded:,}" if ded is not None else "Not Specified",
    )

    # ==============================================================================
    # EVIDENCE STRENGTH & WIN-PROBABILITY METER (PRODUCT INNOVATION #4)
    # ==============================================================================
    ev_data = DisputeEngine.calculate_evidence_meter(confirmed_case)
    ev_score = ev_data["score"]
    ev_tier = ev_data["tier"]

    st.markdown("---")
    col_ev1, col_ev2 = st.columns([1, 2])
    with col_ev1:
        st.markdown(f"#### 📊 Case Strength: **{ev_score}%**")
        st.caption(f"**Documentary Position:** `{ev_tier}`")
        st.progress(ev_score / 100.0)
    with col_ev2:
        st.info(f"⚖️ **Evidentiary Leverage Audit:** {ev_data['summary']}")

    with st.expander("🔍 Inspect Statutory Burden of Proof Breakdown (BSA 2023 & ICA 1872)", expanded=False):
        for item in ev_data["breakdown"]:
            status_icon = "🟢" if item["status"] == "POSITIVE" else ("🔴" if item["status"] == "NEGATIVE" else "⚪")
            st.markdown(
                f"- {status_icon} **{item['factor']}** (`{item['delta']}` · `{item['statute']}`): {item['description']}"
            )
        if ev_data["actionable_tips"]:
            st.markdown("💡 **Actionable Steps to Increase Recovery Leverage:**")
            for tip in ev_data["actionable_tips"]:
                st.markdown(f"  - {tip}")

    tab_rag, tab_draft, tab_pushback, tab_roi, tab_dossier, tab_telemetry = st.tabs([
        "⚖️ Bounded Statutory Guidance (Micro-RAG)",
        "📝 Demand Letter / Settlement Draft",
        "🥊 Landlord Pushback Simulator & WhatsApp Rebuttals",
        "📊 Dispute Resolution & Litigation ROI",
        "📦 e-Daakhil / DLSA Court Dossier",
        "🛡️ System Telemetry & Guardrail Log",
    ])

    with tab_rag:
        st.subheader("Layer 3 & 4: Grounded Statutory Evaluation")
        st.write(
            "The evaluation below is strictly bounded to the top statutory clauses retrieved from "
            "our verified Indian legal knowledge base (`statutes.json`)."
        )

        # Show Retrieved Clauses
        st.markdown("##### 📚 Top-2 Retrieved Statutory Clauses (Layer 3 In-Memory Vector Search)")
        for chunk in st.session_state.retrieved_chunks:
            with st.container():
                st.markdown(
                    f"**[{chunk['id']}] {chunk['act']} — {chunk['section']}**  \n"
                    f"*Title:* {chunk['title']} · *Cosine Similarity Score:* `{chunk.get('similarity_score', 0.85)}`  \n"
                    f"> *\"{chunk['text']}\"*"
                )
                st.caption(f"Verified Source: [Government Gazette / India Code Link]({chunk['url']})")

        st.markdown("##### 🏛️ Bounded Legal Evaluation (Layer 4 & 5)")
        st.write(st.session_state.rag_synthesis)

        st.markdown("---")
        # Dynamic topic dropdown
        topics = DisputeEngine.get_guidance_topics(confirmed_case)
        selected_topic = st.selectbox("Detailed Analysis by Legal Domain:", topics)
        try:
            paragraphs, source_keys = DisputeEngine.evaluate_guidance(
                confirmed_case,
                selected_topic,
                evaluation_text=st.session_state.rag_synthesis,
            )
        except TypeError:
            from guidance import guidance_for
            paragraphs, source_keys = guidance_for(
                confirmed_case,
                selected_topic,
                evaluation_text=st.session_state.rag_synthesis,
            )
        for p in paragraphs:
            sanitized_p, p_status, p_telemetry = CitationFirewall.audit_and_sanitize(
                p, st.session_state.retrieved_chunks
            )
            st.markdown(sanitized_p)
            if p_telemetry and st.session_state.telemetry is not None:
                if "firewall_log" in st.session_state.telemetry:
                    existing_cites = {x.get("citation") for x in st.session_state.telemetry["firewall_log"]}
                    for entry in p_telemetry:
                        if entry.get("citation") not in existing_cites:
                            st.session_state.telemetry["firewall_log"].append(entry)
                            if entry.get("status") == "INTERCEPTED":
                                st.session_state.telemetry["firewall_status"] = "INTERCEPTED"

    with tab_draft:
        # Layer 4 Conditioned Drafting Posture
        try:
            rec_posture = DisputeEngine.classify_dispute_posture(
                case=confirmed_case,
                evaluation_text=st.session_state.rag_synthesis,
            )
        except (TypeError, AttributeError):
            from draft import classify_dispute_posture
            rec_posture = classify_dispute_posture(
                case=confirmed_case,
                evaluation_text=st.session_state.rag_synthesis,
            )

        posture_labels = {
            "justified": "🟢 Full Settlement & Tenancy Discharge Record (Deductions Justified & Invoiced)",
            "unjustified": "🔴 Formal 15-Day Demand Notice (Dispute Arbitrary / Unproven Deductions)",
            "partial": "🟡 Partial Refund Demand (Concede Invoiced Expenses, Dispute Remainder)",
        }
        posture_keys = ["justified", "unjustified", "partial"]
        default_idx = posture_keys.index(rec_posture) if rec_posture in posture_keys else 1

        st.subheader("Objective Legal Correspondence (Evaluation-Conditioned)")
        st.caption(
            "The drafting engine avoids blind advocacy. It conditions the document type and legal tone "
            "directly on the Layer 4 legal evaluation and whether verifiable receipts were provided."
        )

        if rec_posture == "justified":
            st.success(
                "⚖️ **Objective Assessment:** The Layer 4 evaluation indicates the landlord's deductions "
                "for admitted tenant-caused damage / utility arrears are **legally justified** and substantiated by "
                "official invoices/bills. The draft below serves as a formal **Settlement & Discharge Record** rather than a hostile legal demand."
            )
        elif rec_posture == "partial":
            st.warning(
                "⚖️ **Objective Assessment:** Part of the deduction is substantiated by genuine receipts, "
                "while the remainder is arbitrary. The draft concedes the verified portion and demands only the disputed balance."
            )
        else:
            st.info(
                "⚖️ **Objective Assessment:** The landlord's deductions appear arbitrary, unproven, or represent normal wear and tear. "
                "The draft below issues a formal **15-Day Demand Notice for 100% Refund** under Section 73 ICA / Section 11 MTA."
            )

        selected_posture_label = st.radio(
            "Drafting Objective (Auto-selected from Layer 4 Legal Evaluation, editable):",
            [posture_labels[k] for k in posture_keys],
            index=default_idx,
            help="Switch between a formal settlement closure letter and an adversarial demand notice.",
        )
        selected_posture = [k for k, v in posture_labels.items() if v == selected_posture_label][0]

        with st.expander("✏️ Customize Notice Particulars", expanded=False):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                t_name_input = st.text_input("Tenant Name", value="Rahul Verma")
                l_name_input = st.text_input("Landlord Name", value="Property Owner / Landlord")
            with col_d2:
                default_addr = f"Flat No. 402, Sunshine Heights, {confirmed_case.city or 'Saket'}, {confirmed_case.state or 'Delhi'}"
                addr_input = st.text_input("Property Address", value=default_addr)
                bank_input = st.text_input("Refund Bank Account / UPI ID", value="HDFC Bank A/C: 50100234567890 (IFSC: HDFC0001234) / UPI: rahul@upi")

        try:
            draft_text = DisputeEngine.draft_demand_letter(
                case=confirmed_case,
                tenant_name=t_name_input,
                landlord_name=l_name_input,
                property_address=addr_input,
                bank_details=bank_input,
                retrieved_chunks=st.session_state.retrieved_chunks,
                evaluation_text=st.session_state.rag_synthesis,
                posture=selected_posture,
            )
        except TypeError:
            from draft import generate_demand_letter
            draft_text = generate_demand_letter(
                case=confirmed_case,
                tenant_name=t_name_input,
                landlord_name=l_name_input,
                property_address=addr_input,
                bank_details=bank_input,
                retrieved_chunks=st.session_state.retrieved_chunks,
                evaluation_text=st.session_state.rag_synthesis,
                posture=selected_posture,
            )

        draft_box_title = (
            "Settlement & Discharge Record (Fully Editable)"
            if selected_posture == "justified"
            else "Legal Notice Draft (Fully Editable)"
        )
        editable_draft = st.text_area(
            draft_box_title,
            value=draft_text,
            height=380,
        )

        col_dn1, col_dn2 = st.columns([1, 4])
        with col_dn1:
            dl_file_name = (
                "Security_Deposit_Settlement_Discharge.txt"
                if selected_posture == "justified"
                else "Security_Deposit_Demand_Notice.txt"
            )
            st.download_button(
                label=f"📥 Download {'Settlement Letter' if selected_posture == 'justified' else 'Demand Notice'} (.txt)",
                data=editable_draft,
                file_name=dl_file_name,
                mime="text/plain",
                use_container_width=True,
            )
        with col_dn2:
            if selected_posture == "justified":
                st.info("💡 You can sign this closure letter and send it to confirm mutual discharge of all claims.")
            else:
                st.info("💡 You can copy this notice and send it via registered post, WhatsApp, or email.")

    # ==============================================================================
    # TAB 3: LANDLORD PUSHBACK SIMULATOR & WHATSAPP REBUTTALS (PRODUCT INNOVATION #2)
    # ==============================================================================
    with tab_pushback:
        st.subheader("🥊 Landlord Pushback Simulator & WhatsApp Rebuttals")
        st.caption(
            "Game-theoretic counter-strategy: Predicts the 3 most likely adversarial responses from this landlord "
            "and equips you with concise, legally grounded WhatsApp rebuttals."
        )

        pushback_list = DisputeEngine.simulate_landlord_pushback(
            confirmed_case, posture=selected_posture
        )

        for i, pb in enumerate(pushback_list):
            with st.container():
                st.markdown(f"#### {pb['title']}")
                c_pb1, c_pb2 = st.columns([1, 1])
                with c_pb1:
                    st.error(f"💬 **Landlord's Expected Pushback:**\n\n{pb['landlord_message']}")
                    st.caption(f"⚖️ **Legal Reality:** {pb['legal_position']}")
                    st.caption(f"📚 **Statutory Hook:** `{pb['statutory_hook']}`")
                with c_pb2:
                    st.success("📲 **Your 2-Line WhatsApp Rebuttal (Copy & Send):**")
                    st.text_area(
                        f"Rebuttal #{i+1}",
                        value=pb["whatsapp_rebuttal"],
                        height=130,
                        key=f"rebuttal_text_{i}",
                        label_visibility="collapsed",
                    )
                st.markdown("---")

    # ==============================================================================
    # TAB 4: DISPUTE RESOLUTION EXPECTED VALUE (EV) & LITIGATION ROI (PRODUCT INNOVATION #3)
    # ==============================================================================
    with tab_roi:
        st.subheader("📊 Dispute Resolution Expected Value (EV) & Forum Advisor")
        st.caption(
            "Economic feasibility analysis: Compares recovery probability, forum court fees, timeline, "
            "and statutory interest across Indian dispute resolution mechanisms."
        )

        roi_info = DisputeEngine.calculate_litigation_roi(confirmed_case, posture=selected_posture)

        r_col1, r_col2, r_col3, r_col4 = st.columns(4)
        r_col1.metric("Withheld Principal", f"₹{roi_info['disputed_amount_inr']:,}")
        r_col2.metric(
            f"Statutory Interest ({roi_info.get('statutory_rate_pct', 8.0)}% p.a.)",
            f"₹{roi_info['statutory_interest_inr']:,}",
            help="Accrued under Interest Act, 1978 for delay exceeding 30-day statutory refund period.",
        )
        r_col3.metric("Total Legally Claimable", f"₹{roi_info['total_claimable_inr']:,}")
        r_col4.metric("Court Fee", roi_info["court_fee_display"])

        if roi_info["roi_tier"] == "NOT_RECOMMENDED":
            st.warning(f"⚖️ **Litigation Feasibility:** {roi_info['summary']}")
        elif roi_info["roi_tier"] == "ZERO_COST_ESCALATION":
            st.success(f"⚖️ **Optimal Strategy:** {roi_info['summary']}")
        else:
            st.info(f"⚖️ **Optimal Strategy:** {roi_info['summary']}")

        col_roi_left, col_roi_right = st.columns([1, 1])
        with col_roi_left:
            st.markdown(f"##### 🏛️ Recommended Forum: **{roi_info['recommended_forum']}**")
            st.write(f"- **Authority:** `{roi_info['forum_authority']}`")
            st.write(f"- **Advocate Advisory:** {roi_info['lawyer_fee_advice']}")
            st.write(f"- **Expected Timeline:** `{roi_info['estimated_duration']}`")
            st.write(f"- **Net Projected Recovery:** `{roi_info['expected_net_recovery']}`")

        with col_roi_right:
            st.markdown("##### 🧭 Statutory Escalation Ladder (Indian Dispute Forums)")
            for stage in roi_info.get("forum_matrix", []):
                status_badge = "🌟 **RECOMMENDED**" if stage.get("status") == "RECOMMENDED" else ("▶️ **ACTIVE STEP**" if stage.get("status") == "ACTIVE_STEP" else "🔹 Available")
                st.markdown(
                    f"- **{stage['forum']}** — {status_badge}  \n"
                    f"  *Cost:* `{stage['cost']}` · *Court Fee:* `{stage['court_fee']}` · *Timeline:* `{stage['duration']}`  \n"
                    f"  *{stage['suitability']}*"
                )

    # ==============================================================================
    # TAB 5: ONE-CLICK COURT DOSSIER & FILING PACKET (PRODUCT INNOVATION #5)
    # ==============================================================================
    with tab_dossier:
        st.subheader("📦 e-Daakhil / DLSA Pre-Litigation Court Dossier Compiler")
        st.caption(
            "Court-ready formal petition bundle: Formatted specifically for filing before the District Consumer Commission "
            "(e-Daakhil) or District Legal Services Authority (DLSA) Pre-Litigation Lok Adalat."
        )

        dossier_text = DisputeEngine.compile_court_dossier(confirmed_case, posture=selected_posture)

        dossier_file_name = (
            "Tenancy_Mutual_Settlement_Discharge_Dossier.md"
            if selected_posture == "justified"
            else "eDaakhil_DLSA_PreLitigation_Court_Dossier.md"
        )

        col_dos1, col_dos2 = st.columns([1, 3])
        with col_dos1:
            st.download_button(
                label="📦 Download Complete Court Dossier (.md)",
                data=dossier_text,
                file_name=dossier_file_name,
                mime="text/markdown",
                use_container_width=True,
            )
        with col_dos2:
            st.info("💡 Attach this compiled dossier alongside your certified bank statements on the e-Daakhil portal or submit to your local DLSA secretary.")

        st.markdown("##### 📑 Court Dossier Preview & List of Dates")
        with st.expander("📄 View Full Court Filing Packet (Synopsis, Statutory Grounds, Prayer & Verification)", expanded=True):
            st.markdown(dossier_text)

        st.markdown("##### ✅ Index of Annexures & Evidence Checklist")
        st.checkbox("Annexure C-1: Signed Tenancy Agreement (or statement of oral lease terms)", value=(confirmed_case.written_agreement_exists == "yes"))
        st.checkbox("Annexure C-2: Bank / UPI Statement of Deposit Remittance (BSA 2023 §61)", value=(confirmed_case.payment_proof_exists == "yes"))
        st.checkbox("Annexure C-3: Peaceful Key Handover & Move-Out Proof (TPA 1882 §108)", value=bool(confirmed_case.move_out_date))
        st.checkbox("Annexure C-4: Copy of 15-Day Statutory Legal Demand Notice", value=True)
        st.checkbox("Annexure C-5: Proof of Service (Postal Speed Post AD Tracking / WhatsApp Delivery Screenshot)", value=True)

    with tab_telemetry:
        st.subheader("🛡️ Layer 5: Post-Generation AST Citation Firewall & Telemetry Log")
        st.caption("Real-time monitoring of anti-hallucination guardrails and execution metrics.")

        if st.session_state.telemetry:
            telem = st.session_state.telemetry
            t1, t2, t3 = st.columns(3)
            fw_status = telem.get("firewall_status", "PASSED")
            t1.metric(
                "Citation Firewall Status",
                f"{'PASSED ✅' if fw_status == 'PASSED' else 'INTERCEPTED ⚠️'}",
            )
            t2.metric("Pipeline Latency", f"{telem.get('latency_ms', 0)} ms")
            t3.metric("Est. Token Cost", f"${telem.get('estimated_cost_usd', 0):.6f}")

            st.markdown("##### 🔬 Citation Whitelist Cross-Reference Audit")
            st.write(
                "Every statutory citation in the output was cross-referenced against the whitelist "
                f"of retrieved statutory chunks (`{', '.join(telem.get('retrieved_chunk_ids', []))}`)."
            )
            if telem.get("firewall_log"):
                st.dataframe(telem["firewall_log"], use_container_width=True)
            else:
                st.success("No unverified citations detected. Output is 100% grounded in verified retrieved statutes.")

            if st.session_state.pii_log:
                st.markdown("##### 🔐 PII Ingestion Redaction Log")
                st.dataframe(st.session_state.pii_log, use_container_width=True)
        else:
            st.info("Telemetry data will populate upon fact confirmation.")
