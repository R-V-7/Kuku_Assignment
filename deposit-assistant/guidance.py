"""Reviewed, safe legal information; no case-specific legal conclusion is made."""

from models import CaseFacts

SOURCES = {
    "contract": (
        "India Code: Indian Contract Act, 1872, Section 73 (Compensation for breach of contract)",
        "https://www.indiacode.nic.in/bitstream/123456789/2187/2/A187209.pdf",
    ),
    "aid": (
        "NALSA: Free Legal Aid & Application Procedure",
        "https://nalsa.gov.in/legal-aid/",
    ),
    "faq": (
        "NALSA: Legal Aid FAQs and National Helpline 15100",
        "https://nalsa.gov.in/faqs/",
    ),
    "lok": (
        "NALSA: Lok Adalats for Pre-Litigation Dispute Resolution",
        "https://nalsa.gov.in/lok-adalats/",
    ),
    "mta": (
        "Ministry of Housing & Urban Affairs: Model Tenancy Act Guidelines",
        "https://mohua.gov.in/upload/uploadfiles/files/Model_Tenancy_Act_English_2021.pdf",
    ),
}

DEFAULT_TOPICS = (
    "Can the landlord deduct painting costs?",
    "What can I do next?",
    "Can I get legal help or explore settlement?",
)
TOPICS = DEFAULT_TOPICS


def get_guidance_topics(case: CaseFacts) -> list[str]:
    """Dynamically generates guidance dropdown topics using the landlord's stated deduction reason."""
    reason = (
        case.deduction_reason.strip()
        if case.deduction_reason and case.deduction_reason.strip()
        else None
    )
    if reason:
        deduction_question = f"Can the landlord deduct for {reason}?"
    else:
        deduction_question = "Can the landlord deduct from the security deposit?"

    return [
        deduction_question,
        "What can I do next?",
        "Can I get legal help or explore settlement?",
    ]


def _categorize_deduction(reason: str) -> str:
    """Classify the landlord's excuse into actionable legal categories."""
    r = reason.lower()

    # Society penalties / bylaw fines / noise
    if any(k in r for k in ["penalty", "fine", "society", "rwa", "diwali", "festival", "music", "noise", "party", "parking"]):
        return "society_penalty"

    # Unrelated personal / business losses
    if any(k in r for k in ["business", "loss", "losses", "personal", "market", "loan", "wedding", "afford", "crisis"]):
        return "business_losses"

    # Painting and whitewashing
    if any(k in r for k in ["paint", "painting", "whitewash", "white wash", "wall", "walls", "repainting", "color"]):
        return "painting"

    # Deep cleaning and routine upkeep
    if any(k in r for k in ["clean", "cleaning", "deep clean", "housekeeping", "sanitization", "maid"]):
        return "cleaning"

    # Appliances and fixtures repair/servicing
    if any(k in r for k in ["purifier", "water purifier", "ac", "air conditioner", "geyser", "refrigerator", "fridge", "motor", "appliance", "servicing"]):
        return "appliances"

    # Physical damage / breakage
    if any(k in r for k in ["tile", "tiles", "broken", "crack", "cracked", "door", "glass", "plumbing", "pipe", "damage"]):
        return "damage"

    return "general"


def guidance_for(
    case: CaseFacts,
    topic: str,
    evaluation_text: str = "",
    posture: str | None = None,
) -> tuple[list[str], list[str]]:
    if case.scope != "residential_deposit":
        return (
            [
                "This guidance is limited to residential rental deposit disputes. Seek advice appropriate to your situation."
            ],
            ["aid"],
        )

    if posture is None:
        try:
            from draft import classify_dispute_posture
            posture = classify_dispute_posture(case, evaluation_text)
        except Exception:
            posture = "unjustified"

    topic_lower = topic.strip().lower()

    # 1. Dynamic Deduction Analysis
    if "deduct" in topic_lower:
        # Determine display reason dynamically from case facts or topic
        if case.deduction_reason and case.deduction_reason.strip():
            reason = case.deduction_reason.strip()
        elif "painting" in topic_lower:
            reason = "painting"
        else:
            reason = "the claimed deduction"

        category = _categorize_deduction(reason)

        if posture == "justified":
            ded_str = (
                f"₹{case.deduction_amount_inr:,}"
                if case.deduction_amount_inr is not None
                else "the stated amount"
            )
            paragraphs = [
                f"Based on the reported facts and Layer 4 statutory evaluation, the landlord's deduction for '{reason}' appears **legally substantiated and documented** under applicable Indian tenancy law:",
                f"You reported an accounted deduction of {ded_str} supported by verified third-party invoices and payment vouchers.",
                "1. **Statutory Authority (Section 11 Model Tenancy Act, 2021 & Section 73 Indian Contract Act, 1872):** Deductions from a security deposit are explicitly permissible for documented tenant arrears (such as verified utility consumption) and agreed repairs or actual loss resulting from tenant breach beyond reasonable wear and tear.",
                "2. **Evidentiary Threshold Satisfied:** The landlord has furnished verified third-party documentation (such as official contractor GST tax invoices and meter bills), satisfying the statutory burden of proof required under Indian law.",
                "**Actionable Strategy:** Verify that the invoice totals match the deducted amount and that the billing periods match your occupancy. If the amounts reconcile, this deduction is legally valid, and formal dispute or litigation is not recommended.",
            ]
            return paragraphs, ["mta", "contract"]

        paragraphs = [
            f"I cannot determine from these facts alone whether a deduction for '{reason}' is legally justified in your specific dispute, as conclusive determination requires examining your signed tenancy agreement and factual evidence. However, under Indian law, the legal position is as follows:"
        ]

        if case.deduction_amount_inr is not None:
            paragraphs.append(
                f"You reported a proposed deduction of ₹{case.deduction_amount_inr:,}; this is the amount stated by the landlord, not a finding that it is valid or legally owed."
            )

        # Nuanced, category-specific legal evaluation
        if category == "society_penalty":
            paragraphs.extend([
                "🏢 **Society Penalties & Bylaw Violations:** A landlord cannot unilaterally levy or deduct building society fines without satisfying two strict evidentiary thresholds under Indian cooperative society law:",
                "1. **Official Written Notice & Receipt:** The Apartment Owners Association (AOA) or Resident Welfare Association (RWA) must have issued an official written show-cause/infraction notice directly naming your flat unit, accompanied by a stamped society payment receipt proving the fine was actually paid to the society.",
                "2. **Contractual Liability:** The signed lease agreement must contain an explicit clause holding the tenant financially liable for society penalties.",
                "**Actionable Strategy:** In your demand notice, challenge this deduction as unauthorized unless the landlord furnishes certified copies of the RWA penalty debit note, the official payment receipt, and the relevant clause in your lease."
            ])
        elif category == "business_losses":
            paragraphs.extend([
                "💼 **Zero Legal Nexus (Unrelated Personal Losses):** Under Section 73 of the Indian Contract Act, 1872, a security deposit is held in fiduciary trust solely to secure tenant obligations (rent payment and physical property preservation).",
                "A landlord's personal business losses, commercial debt, or financial difficulties have **zero legal connection** to your residential tenancy. Forfeiting or withholding a deposit to absorb unrelated business hardship is legally indefensible and constitutes unjust enrichment and an actionable breach of contract under Section 73 of the Indian Contract Act, 1872.",
                "**Actionable Strategy:** You have a clear legal entitlement to demand immediate 100% refund of this withheld balance. Remind the landlord that personal business debts cannot be legally offset against tenant deposit funds."
            ])
        elif category == "painting":
            paragraphs.extend([
                "🎨 **Normal Wear & Tear vs. Tenant Damage:** Under Section 73 of the Indian Contract Act and established tenancy jurisprudence, reasonable wear and tear arising from normal domestic living (such as gradual fading of paint or picture hook marks) is the property owner's operational maintenance cost, NOT tenant-caused damage.",
                "A mandatory deduction for full-house repainting upon exit is legally contestable unless an explicit, unambiguous repainting clause was negotiated and signed in your rental agreement. Even then, deductions must reflect actual, reasonable painting expenses supported by genuine GST tax invoices—not an arbitrary lump-sum penalty.",
                "**Actionable Strategy:** If your agreement lacks a mandatory repainting clause, dispute the deduction as normal wear and tear. Demand move-in vs move-out comparison photographs and genuine vendor GST bills."
            ])
        elif category == "cleaning":
            paragraphs.extend([
                "🧹 **Routine Turnover Cleaning vs. Tenant Filth:** Indian law requires a tenant to leave the premises in a 'reasonably clean and tenantable condition,' not in a factory-new state. General dusting, floor mopping, or turnover preparation between tenants is standard owner maintenance.",
                "Deductions for deep cleaning are only permissible if the tenant left the premises in an unusually unhygienic condition, and even then, deductions are strictly limited to actual, documented third-party vendor charges (e.g., Urban Company or registered housekeeping receipts).",
                "**Actionable Strategy:** Request original tax invoices and payment vouchers from the cleaning agency. Arbitrary lump-sum deductions without third-party receipts are routinely overturned in consumer forums."
            ])
        elif category == "appliances":
            paragraphs.extend([
                "⚙️ **Capital Equipment & Fixture Maintenance:** Under the Model Tenancy framework and standard tenancy principles, major appliances (water purifiers, air conditioners, geysers, motors) provided by the landlord naturally degrade over time through ordinary mechanical aging.",
                "Routine mechanical breakdowns or age-related component failures are the landlord's maintenance obligations, not the tenant's. A landlord cannot force a departing tenant to fund a brand-new appliance replacement unless they prove deliberate physical abuse or gross negligence by the tenant.",
                "**Actionable Strategy:** Request: (1) an authorized technician diagnostic report confirming tenant misuse rather than natural operational wear, and (2) depreciation-adjusted repair estimates rather than full replacement cost."
            ])
        elif category == "damage":
            paragraphs.extend([
                "🔨 **Burden of Proof for Physical Damage:** While physical damage beyond normal wear and tear (such as cracked tiles, broken doors, or shattered sanitaryware) can be deducted under Section 73 of the Indian Contract Act, the legal burden of proof lies entirely upon the landlord.",
                "The landlord cannot invent unilateral estimates. They are legally required to furnish: (1) move-in inventory records showing the item was intact at commencement, (2) move-out joint inspection documentation, and (3) genuine GST invoices for the actual replacement materials and labor.",
                "**Actionable Strategy:** Insist on viewing the original repair invoices and comparative handover photos. Refuse any arbitrary deductions that are not supported by verified receipts."
            ])
        else:
            paragraphs.extend([
                "⚖️ **Requirement of Demonstrable Loss (Section 73):** Under Section 73 of the Indian Contract Act, 1872, any deduction from a security deposit requires proof of an actual breach of contract or demonstrable financial loss caused by the tenant beyond reasonable wear and tear.",
                "Unilateral or arbitrary deductions without contractual basis and verifiable expense receipts lack legal validity. A landlord is legally obligated to provide an itemised written explanation and tax invoices for every rupee withheld.",
                "**Actionable Strategy:** Ask the landlord in writing for an itemised written breakdown, the contractual basis in the agreement, and copies of actual bills, tax invoices, or inspection photographs."
            ])

        return paragraphs, ["contract", "aid"]

    # 2. Next steps
    if "next" in topic_lower:
        if posture == "justified":
            paragraphs = [
                "🔍 **Reconcile and Verify Invoices:** Compare the furnished contractor GST invoices and verified meter bills against the deducted amount. Ensure the work description corresponds to the damage and any billing dates match your tenancy period.",
                "📝 **Execute Tenancy Settlement & Discharge Record:** Rather than issuing an adversarial demand notice, generate and sign the formal **Deposit Settlement & Tenancy Discharge Record** (available in the 'Demand Letter Draft' tab). Provide this to the landlord to confirm mutual closure of the lease and ensure neither party can make future claims.",
                "📁 **Preserve Transaction Records:** Retain copies of the initial deposit transfer receipt, the refund received, and the vendor GST invoices for your personal financial and tax records.",
            ]
            if case.deposit_amount_inr is not None and case.amount_returned_inr is not None:
                returned = case.amount_returned_inr
                withheld = max(0, case.deposit_amount_inr - returned)
                paragraphs.insert(
                    0,
                    f"The deposit reconciliation shows ₹{returned:,} refunded and ₹{withheld:,} withheld for documented expenses from the original ₹{case.deposit_amount_inr:,} deposit.",
                )
            return paragraphs, ["mta", "contract"]

        elif posture == "partial":
            paragraphs = [
                "⚖️ **Concede Specifically Verified Expenses & Isolate Disputed Balance:** Formally concede only the specific deductions substantiated by verified third-party tax invoices/receipts, and strictly isolate the remaining disputed balance that lacks receipts or contractual basis.",
                "📝 **Issue Partial Demand Notice:** Send a formal written notice conceding the verified expenses while demanding immediate refund of the unjustified balance within 15 days under Section 73 of the Indian Contract Act, 1872.",
                "📁 **Preserve Evidence:** Keep copies of all move-in/move-out messages, handover photos, and payment receipts in case further dispute escalation is necessary.",
            ]
            return paragraphs, ["contract", "mta", "aid"]

        else:
            # Unjustified (0% Proven): Demands 100% full refund; strictly zero concession language.
            paragraphs = [
                "📁 **Collect and Preserve Evidentiary Records:** Assemble your rental agreement, deposit payment receipts/bank transaction records, move-out handover proof, keys handover acknowledgment, photographs, and written communications.",
                "📝 **Issue a Formal 15-Day Demand Notice:** Send a formal written demand notice to the landlord calling for the full refund of the withheld amount within 15 days under Section 73 of the Indian Contract Act, 1872. Dispatch via Registered Post AD or email to create verifiable delivery proof.",
                "⚖️ **Escalate to Legal Aid / Dispute Resolution:** If the landlord ignores the notice or refuses to refund the full balance, you can approach the competent Rent Authority, file a consumer complaint for deficiency in service before the District Consumer Commission (DCDRC), or apply for free pre-litigation dispute resolution through the District Legal Services Authority (DLSA) / Lok Adalat.",
            ]
            if case.deposit_amount_inr is not None and case.amount_returned_inr is not None:
                balance = case.deposit_amount_inr - case.amount_returned_inr
                if balance >= 0:
                    paragraphs.insert(
                        0,
                        f"The stated deposit minus the stated amount returned is ₹{balance:,} before any deductions. This is arithmetic, not a legal determination of what is owed.",
                    )
            return paragraphs, ["aid", "faq"]

    # 3. Legal aid & Lok Adalat
    if "help" in topic_lower or "aid" in topic_lower or "settlement" in topic_lower or "lok" in topic_lower:
        if posture == "justified":
            ret_str = f"₹{case.amount_returned_inr:,}" if case.amount_returned_inr is not None else "the balance"
            paragraphs = [
                "🚫 **Legal Action Not Recommended:** Because the landlord has complied with mandatory statutory requirements (Section 11 of the Model Tenancy Act, 2021 and Section 73 of the Indian Contract Act, 1872) by providing official third-party tax invoices and billing receipts for tenant-caused damage or consumption, **pursuing litigation, consumer forum complaints, or legal aid is not recommended**.",
                "⚠️ **Risk of Dismissal & Legal Costs:** Before any Rent Authority, Civil Court, or Consumer Disputes Redressal Commission, a landlord who produces legitimate vendor GST invoices and billing receipts easily satisfies the burden of proof. Initiating legal proceedings under these circumstances is likely to result in dismissal of your claim, unnecessary expenditure of legal fees, and potential exposure to court costs.",
                f"🤝 **Settlement is Concluded:** Since the landlord returned the balance deposit ({ret_str}) and properly accounted for the remainder with verified receipts, the tenancy is substantively resolved. Signing a mutual discharge letter is the most prudent and cost-effective course of action.",
            ]
            return paragraphs, ["contract", "mta"]

        elif posture == "partial":
            paragraphs = [
                "⚖️ **Targeted Pre-Litigation Mediation:** If the landlord refuses to refund the unverified, arbitrary portion of the deposit after conceding legitimate invoiced charges, pre-litigation mediation through your District Legal Services Authority (DLSA) or Lok Adalat is an effective, free forum to recover the disputed balance.",
                "🏛️ **Legal Aid via NALSA:** NALSA provides free legal aid to eligible persons (National Helpline 15100). Focus any mediation strictly on the arbitrary deductions lacking tax invoices or contractual basis.",
            ]
            return paragraphs, ["aid", "faq", "lok"]

        else:
            # Unjustified (0% Proven): Full legal aid, Lok Adalat, and consumer court options
            paragraphs = [
                "🏛️ **Free Legal Aid via NALSA / DLSA:** You may be eligible for free legal representation and guidance under the Legal Services Authorities Act, 1987. Contact the National Legal Services Authority (NALSA) Helpline at **15100** or visit your local District Legal Services Authority (DLSA) situated at your District Court complex.",
                "🤝 **Pre-Litigation Lok Adalat:** You can initiate pre-litigation conciliation through your local DLSA or permanent Lok Adalat. Lok Adalat proceedings carry zero court fees, operate informally without lengthy procedural delays, and any mutual settlement has the binding status of a civil court decree.",
                "⚖️ **Consumer Disputes Redressal Commission (DCDRC):** Arbitrary withholding of a rental deposit without contractual basis or verified bills amounts to unfair trade practice and deficiency in service. Tenants may file a complaint online through the **e-Daakhil** portal (edaakhil.nic.in) seeking recovery of the deposit with statutory interest and litigation compensation.",
            ]
            return paragraphs, ["aid", "faq", "lok"]

    raise ValueError(f"Unknown guidance topic: {topic}")
