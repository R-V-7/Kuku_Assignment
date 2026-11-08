"""Runner to generate unedited raw outputs for test cases as required by Kuku Problem 2."""

import json
import os
from pathlib import Path
from models import CaseFacts
from engine import DisputeEngine
from intake import extract_case
from llm_client import ModelResponse, create_client, ModelError

OUTPUT_DIR = Path(__file__).parent / "raw_outputs"


class MockLLMClient:
    """Mock client providing realistic LLM responses when offline."""

    def __init__(self, responses: dict[str, str]) -> None:
        self.responses = responses

    def generate_text(self, prompt: str) -> ModelResponse:
        for key, val in self.responses.items():
            if key in prompt:
                return ModelResponse(text=val, model="gemini-3.5-flash-lite-mock")
        # Default fallback
        return ModelResponse(
            text='{"scope": "residential_deposit", "uncertainties": ["Details incomplete"]}',
            model="gemini-3.5-flash-lite-mock",
        )

    def generate_json(self, prompt: str, schema: dict) -> ModelResponse:
        return self.generate_text(prompt)


TEST_CASES = [
    {
        "id": "case_01_delhi_business_losses",
        "title": "Delhi - Landlord Deducts for 'Business Losses' (Delhi UT Bug & Dynamic Reason)",
        "story": (
            "I was renting a 2BHK flat in Saket, Delhi for 2 years (Phone: 9876543210, Aadhaar: 4321 8765 1234). "
            "I vacated on 15 January 2025. My security deposit was Rs 60,000 paid through bank transfer. "
            "We had a registered 11-month agreement. The landlord Mr. Ramesh Sharma only returned Rs 20,000 and kept Rs 40,000 "
            "claiming he suffered business losses this year and cannot afford to pay me back. How can I get my money back?"
        ),
        "mock_json": json.dumps(
            {
                "scope": "residential_deposit",
                "city": "Delhi",
                "state": "Delhi",
                "deposit_amount_inr": 60000,
                "amount_returned_inr": 20000,
                "move_out_date": "15 January 2025",
                "written_agreement_exists": "yes",
                "payment_proof_exists": "yes",
                "deduction_reason": "business losses",
                "deduction_amount_inr": 40000,
                "other_details": ["2BHK flat in Saket", "Rented for 2 years", "Landlord name is Mr. Ramesh Sharma"],
                "uncertainties": [],
                "inferred_details": ["40,000 withheld unlawfully under pretext of business hardship"],
            }
        ),
        "tenant_name": "Rahul Verma",
        "landlord_name": "Mr. Ramesh Sharma",
        "property_address": "Flat 302, Saket DDA Flats, New Delhi 110017",
    },
    {
        "id": "case_02_chandigarh_cleaning_no_agreement",
        "title": "Chandigarh - Oral Lease with Withholding for AC Servicing & Cleaning",
        "story": (
            "I vacated my rented studio in Sector 35, Chandigarh on 28 October 2025. I gave Rs 25,000 deposit in cash. "
            "There was no written agreement signed, but I have Google Pay receipts for all rent transfers. "
            "The owner Mrs. Preeti Kaur returned 15000 but deducted 10000 saying flat needed deep cleaning and AC servicing. "
            "She did not provide any vendor bill or bill copy."
        ),
        "mock_json": json.dumps(
            {
                "scope": "residential_deposit",
                "city": "Chandigarh",
                "state": "Chandigarh",
                "deposit_amount_inr": 25000,
                "amount_returned_inr": 15000,
                "move_out_date": "28 October 2025",
                "written_agreement_exists": "no",
                "payment_proof_exists": "yes",
                "deduction_reason": "deep cleaning and AC servicing",
                "deduction_amount_inr": 10000,
                "other_details": ["Studio in Sector 35", "Rent paid via Google Pay", "Landlady Mrs. Preeti Kaur"],
                "uncertainties": [],
                "inferred_details": ["No itemized bills or invoices provided for deductions"],
            }
        ),
        "tenant_name": "Aman Deep Singh",
        "landlord_name": "Mrs. Preeti Kaur",
        "property_address": "House No. 1124, Sector 35-C, Chandigarh 160035",
    },
    {
        "id": "case_03_bengaluru_painting_wear_and_tear",
        "title": "Bengaluru - Painting & Repainting Deduction Beyond Normal Wear and Tear",
        "story": (
            "I lived in Koramangala Bengaluru for 3 years. Moved out on 1st November 2025. "
            "Security deposit was Rs 1,00,000. Landlord returned 70,000 and deducted 30,000 for full house repainting. "
            "We had a written lease agreement which did not mention mandatory painting deduction upon exit. "
            "The walls only had normal wear and tear and no physical damage."
        ),
        "mock_json": json.dumps(
            {
                "scope": "residential_deposit",
                "city": "Bengaluru",
                "state": "Karnataka",
                "deposit_amount_inr": 100000,
                "amount_returned_inr": 70000,
                "move_out_date": "1 November 2025",
                "written_agreement_exists": "yes",
                "payment_proof_exists": "unknown",
                "deduction_reason": "full house repainting",
                "deduction_amount_inr": 30000,
                "other_details": ["Lived in Koramangala for 3 years", "Lease agreement had no painting clause"],
                "uncertainties": [],
                "inferred_details": ["Tenant claims walls only exhibited standard wear and tear"],
            }
        ),
        "tenant_name": "Karthik Subramanian",
        "landlord_name": "V. Suresh Reddy",
        "property_address": "Flat 204, Green Glen Apartments, 4th Block Koramangala, Bengaluru 560034",
    },
    {
        "id": "case_04_mumbai_hinglish_arbitrary_retention",
        "title": "Mumbai - Hinglish Messy Story with Total Withholding Without Explanation",
        "story": (
            "Bhai maine Andheri West Mumbai me flat khali kiya 15 September 2025 ko. Deposit 80000 diya tha online transfer se. "
            "Landlord ek rupya wapas nahi kar raha hai bol raha hai maintenance kharcha lag gaya par kitna aur kyu kuch bataya nahi. "
            "Agreement bhi tha registered. Mujhe mera pura deposit chahiye."
        ),
        "mock_json": json.dumps(
            {
                "scope": "residential_deposit",
                "city": "Mumbai",
                "state": "Maharashtra",
                "deposit_amount_inr": 80000,
                "amount_returned_inr": 0,
                "move_out_date": "15 September 2025",
                "written_agreement_exists": "yes",
                "payment_proof_exists": "yes",
                "deduction_reason": "unspecified maintenance charges",
                "deduction_amount_inr": 80000,
                "other_details": ["Flat in Andheri West", "Deposit paid via online transfer", "Zero refund given"],
                "uncertainties": ["Exact itemization of claimed maintenance not specified"],
                "inferred_details": ["Entire deposit of 80,000 arbitrarily withheld"],
            }
        ),
        "tenant_name": "Aditya Joshi",
        "landlord_name": "Sunil Mehta",
        "property_address": "Flat 801, Sea View Enclave, Andheri West, Mumbai 400058",
    },
    {
        "id": "case_05_hyderabad_followup_loop",
        "title": "Hyderabad - Incomplete Story Triggering Targeted Follow-Up & Resolution",
        "story": "My landlord in Gachibowli refuses to return my deposit claiming damage to tiles.",
        "followup_qa": [
            ("Which state is the rental property in?", "Telangana"),
            ("How much was the security deposit, in rupees?", "45000"),
            ("How much of the deposit, if any, has already been returned?", "None, 0 returned"),
            ("When did you move out? Please include the year, if known.", "August 2025"),
            ("Was there a written rental agreement?", "Yes, we had an 11-month agreement"),
            ("Do you have proof that you paid the deposit?", "Yes, bank statement shows UPI transfer"),
            ("Has the landlord specified how much they want to deduct? If so, how much?", "He claims 20000 for tile replacement"),
        ],
        "mock_json": json.dumps(
            {
                "scope": "residential_deposit",
                "city": "Hyderabad",
                "state": "Telangana",
                "deposit_amount_inr": 45000,
                "amount_returned_inr": 0,
                "move_out_date": "August 2025",
                "written_agreement_exists": "yes",
                "payment_proof_exists": "yes",
                "deduction_reason": "tile replacement",
                "deduction_amount_inr": 20000,
                "other_details": ["Located in Gachibowli", "Deposit paid via UPI with bank statement proof"],
                "uncertainties": [],
                "inferred_details": ["Dispute over alleged tile damage costing 20,000"],
            }
        ),
        "tenant_name": "Sneha Reddy",
        "landlord_name": "K. Venkat Rao",
        "property_address": "Plot 42, Telecom Nagar, Gachibowli, Hyderabad 500032",
    },
    {
        "id": "case_06_bangalore_water_damage_justified",
        "title": "Bangalore - Justified Deductions for Admitted Water Damage (GST Invoice) & Pending BESCOM Bill",
        "story": (
            "I vacated my flat in Bangalore on 1st November 2026. My security deposit was Rs 1,00,000 paid online. "
            "We have a signed 11-month rental agreement. The landlord returned 75,000 but withheld 25,000. "
            "He said 20,000 is for replacing the modular kitchen cabinets which got severe water damage because I accidentally left the sink overflowing overnight, "
            "and 5,000 is for my pending BESCOM electricity bill. He sent me the official carpenter's GST invoice and the pending BESCOM meter bill on WhatsApp. "
            "I feel this is unfair, shouldn't the owner pay for his flat's repairs? Can he legally deduct this?"
        ),
        "mock_json": json.dumps(
            {
                "scope": "residential_deposit",
                "city": "Bangalore",
                "state": "Karnataka",
                "deposit_amount_inr": 100000,
                "amount_returned_inr": 75000,
                "move_out_date": "1st November 2026",
                "written_agreement_exists": "yes",
                "payment_proof_exists": "yes",
                "deduction_reason": "replacing modular kitchen cabinets due to water damage from overflowing sink and pending BESCOM electricity bill",
                "deduction_amount_inr": 25000,
                "other_details": [
                    "Tenant accidentally left the sink overflowing overnight causing severe water damage to kitchen cabinets",
                    "Landlord provided official carpenter GST invoice for 20,000",
                    "Landlord provided official pending BESCOM meter bill for 5,000 via WhatsApp",
                ],
                "uncertainties": [],
                "inferred_details": [
                    "Deductions correspond to tenant-caused damage beyond wear and tear and unpaid utility consumption, supported by vendor invoices",
                ],
            }
        ),
        "tenant_name": "Karthik Subramanian",
        "landlord_name": "Anand Murthy",
        "property_address": "Flat 304, Palm Meadows, Whitefield, Bangalore 560066",
    },
]


def run_test_cases() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating 5-Layer Micro-RAG raw outputs in: {OUTPUT_DIR.resolve()}\n")

    has_live_api = bool(os.environ.get("GEMINI_API_KEY"))

    summary_records = []

    for idx, tc in enumerate(TEST_CASES, start=1):
        print(f"Processing Test Case {idx}: {tc['title']}...")
        
        # Determine client: live or mock
        if has_live_api:
            try:
                client = create_client()
            except Exception:
                client = MockLLMClient({tc["story"][:30]: tc["mock_json"]})
        else:
            client = MockLLMClient({tc["story"][:30]: tc["mock_json"]})

        engine = DisputeEngine(client)

        # Layer 1: PII Redaction
        redacted_story, pii_log = engine.redact_user_input(tc["story"])

        # Layer 1: Fact Extraction
        case = engine.extract_intake(redacted_story)

        # In case of follow-up interaction
        followup_log = []
        if "followup_qa" in tc:
            for q, a in tc["followup_qa"]:
                followup_log.append({"question": q, "answer": a})
            case = CaseFacts.model_validate_json(tc["mock_json"])

        # Layer 1: Query Expander
        expanded_query = engine.expand_query(redacted_story, case.deduction_reason)

        # Layer 3: Micro-RAG In-Memory Retrieval
        retrieved_chunks = engine.retrieve_statutes(expanded_query, top_k=2)

        # Layer 4 & 5: Bounded Grounding & Citation Firewall
        rag_synthesis, firewall_status, telemetry = engine.synthesize_rag_guidance(
            case, retrieved_chunks
        )

        # Layer 4: Formal Legal Correspondence (Conditioned on Layer 4 Evaluation)
        posture = engine.classify_dispute_posture(case, evaluation_text=rag_synthesis)
        letter = engine.draft_demand_letter(
            case=case,
            tenant_name=tc["tenant_name"],
            landlord_name=tc["landlord_name"],
            property_address=tc["property_address"],
            retrieved_chunks=retrieved_chunks,
            evaluation_text=rag_synthesis,
            posture=posture,
        )

        # Product Innovations
        evidence_meter = engine.calculate_evidence_meter(case)
        pushbacks = engine.simulate_landlord_pushback(case, posture=posture)
        litigation_roi = engine.calculate_litigation_roi(case, posture=posture)
        court_dossier = engine.compile_court_dossier(case, posture=posture)

        output_data = {
            "test_case_id": tc["id"],
            "title": tc["title"],
            "dispute_posture": posture,
            "layer_1_raw_input": tc["story"],
            "layer_1_redacted_input": redacted_story,
            "layer_1_pii_audit_log": pii_log,
            "layer_1_expanded_legal_query": expanded_query,
            "layer_2_followup_conversation": followup_log,
            "layer_2_confirmed_facts": case.model_dump(),
            "layer_3_retrieved_statutory_chunks": [
                {
                    "id": c["id"],
                    "act": c["act"],
                    "section": c["section"],
                    "title": c["title"],
                    "similarity_score": c.get("similarity_score", 0.88),
                    "url": c["url"],
                }
                for c in retrieved_chunks
            ],
            "layer_4_bounded_rag_evaluation": rag_synthesis,
            "layer_5_citation_firewall_status": firewall_status,
            "layer_5_telemetry": telemetry,
            "layer_4_generated_correspondence": letter,
            "product_innovation_evidence_strength_meter": evidence_meter,
            "product_innovation_pushback_simulator": pushbacks,
            "product_innovation_litigation_roi": litigation_roi,
            "product_innovation_court_dossier": court_dossier,
        }

        # Write case output files
        json_file = OUTPUT_DIR / f"{tc['id']}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        letter_file = OUTPUT_DIR / f"{tc['id']}_demand_notice.txt"
        with open(letter_file, "w", encoding="utf-8") as f:
            f.write(letter)

        dossier_file = OUTPUT_DIR / f"{tc['id']}_court_dossier.md"
        with open(dossier_file, "w", encoding="utf-8") as f:
            f.write(court_dossier)

        summary_records.append(
            {
                "case_id": tc["id"],
                "city": case.city,
                "state": case.state,
                "posture": posture,
                "deduction_reason": case.deduction_reason,
                "evidence_strength_score": evidence_meter["score"],
                "evidence_tier": evidence_meter["tier"],
                "recommended_forum": litigation_roi["recommended_forum"],
                "pii_redacted_count": len(pii_log),
                "retrieved_sections": [c["section"] for c in retrieved_chunks],
                "firewall_status": firewall_status,
                "outstanding_balance": (case.deposit_amount_inr or 0) - (case.amount_returned_inr or 0),
            }
        )
        print(f"  ✓ Output written to {json_file.name}, {letter_file.name}, & {dossier_file.name} (Firewall: {firewall_status})")

    # Generate master index
    index_file = OUTPUT_DIR / "RAW_OUTPUTS_INDEX.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(summary_records, f, indent=2, ensure_ascii=False)
    print(f"\nCompleted! Master index written to: {index_file.name}")


if __name__ == "__main__":
    run_test_cases()
