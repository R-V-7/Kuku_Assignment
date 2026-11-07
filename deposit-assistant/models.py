"""Case information proposed by the model, pending user confirmation."""

import re
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Indian Union Territories / City-states that should satisfy both city and state
UNION_TERRITORIES: dict[str, str] = {
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "nct of delhi": "Delhi",
    "national capital territory of delhi": "Delhi",
    "chandigarh": "Chandigarh",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "lakshadweep": "Lakshadweep",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "ladakh": "Ladakh",
    "jammu and kashmir": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
}

# Major Indian tech & rental hubs mapped to their respective States
MAJOR_INDIAN_CITIES_TO_STATE: dict[str, str] = {
    # Maharashtra
    "pune": "Maharashtra",
    "mumbai": "Maharashtra",
    "navi mumbai": "Maharashtra",
    "thane": "Maharashtra",
    "nagpur": "Maharashtra",
    "nashik": "Maharashtra",
    "aurangabad": "Maharashtra",
    "chhatrapati sambhajinagar": "Maharashtra",
    "solapur": "Maharashtra",
    "kolhapur": "Maharashtra",
    # Karnataka
    "bengaluru": "Karnataka",
    "bangalore": "Karnataka",
    "mysuru": "Karnataka",
    "mysore": "Karnataka",
    "hubli": "Karnataka",
    "dharwad": "Karnataka",
    "mangalore": "Karnataka",
    "mangaluru": "Karnataka",
    "belgaum": "Karnataka",
    "belagavi": "Karnataka",
    # Telangana
    "hyderabad": "Telangana",
    "secunderabad": "Telangana",
    "cyberabad": "Telangana",
    "warangal": "Telangana",
    # Tamil Nadu
    "chennai": "Tamil Nadu",
    "madras": "Tamil Nadu",
    "coimbatore": "Tamil Nadu",
    "madurai": "Tamil Nadu",
    "tiruchirappalli": "Tamil Nadu",
    "trichy": "Tamil Nadu",
    "salem": "Tamil Nadu",
    # West Bengal
    "kolkata": "West Bengal",
    "calcutta": "West Bengal",
    "howrah": "West Bengal",
    "siliguri": "West Bengal",
    # NCR / Haryana
    "gurgaon": "Haryana",
    "gurugram": "Haryana",
    "faridabad": "Haryana",
    "panipat": "Haryana",
    # NCR / Uttar Pradesh
    "noida": "Uttar Pradesh",
    "greater noida": "Uttar Pradesh",
    "ghaziabad": "Uttar Pradesh",
    "lucknow": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh",
    "varanasi": "Uttar Pradesh",
    "agra": "Uttar Pradesh",
    "prayagraj": "Uttar Pradesh",
    "allahabad": "Uttar Pradesh",
    # Gujarat
    "ahmedabad": "Gujarat",
    "surat": "Gujarat",
    "vadodara": "Gujarat",
    "baroda": "Gujarat",
    "rajkot": "Gujarat",
    "gandhinagar": "Gujarat",
    # Rajasthan
    "jaipur": "Rajasthan",
    "jodhpur": "Rajasthan",
    "udaipur": "Rajasthan",
    "kota": "Rajasthan",
    # Kerala
    "kochi": "Kerala",
    "cochin": "Kerala",
    "ernakulam": "Kerala",
    "thiruvananthapuram": "Kerala",
    "trivandrum": "Kerala",
    "kozhikode": "Kerala",
    # Madhya Pradesh
    "indore": "Madhya Pradesh",
    "bhopal": "Madhya Pradesh",
    "gwalior": "Madhya Pradesh",
    # Bihar & Jharkhand
    "patna": "Bihar",
    "ranchi": "Jharkhand",
    "jamshedpur": "Jharkhand",
    # Odisha
    "bhubaneswar": "Odisha",
    "cuttack": "Odisha",
    # Andhra Pradesh
    "visakhapatnam": "Andhra Pradesh",
    "vizag": "Andhra Pradesh",
    "vijayawada": "Andhra Pradesh",
    # Punjab
    "amritsar": "Punjab",
    "ludhiana": "Punjab",
    "jalandhar": "Punjab",
    # Uttarakhand & Himachal
    "dehradun": "Uttarakhand",
    "shimla": "Himachal Pradesh",
    # Assam & Northeast
    "guwahati": "Assam",
    # Goa
    "panaji": "Goa",
    "panjim": "Goa",
}


INVALID_LOCATION_WORDS = {"yes", "no", "unknown", "none", "na", "n/a", "nil", "null", "false", "true"}


def clean_location_input(city: str | None, state: str | None) -> tuple[str | None, str | None]:
    """Parse out natural language phrases like 'City is Mumbai and state is Maharashtra'."""
    combined = ""
    if city and any(k in str(city).lower() for k in ["city is", "state is", "city:"]):
        combined = str(city)
    elif state and any(k in str(state).lower() for k in ["city is", "state is", "state:"]):
        combined = str(state)

    if combined:
        c_m = re.search(r"city\s*(?:is|:)?\s*([A-Za-z\s]+?)(?:\s+and\s+|\s*,\s*|\s*state|\.|\Z)", combined, re.I)
        s_m = re.search(r"state\s*(?:is|:)?\s*([A-Za-z\s]+?)(?:\s+and\s+|\s*,\s*|\s*city|\.|\Z)", combined, re.I)
        if c_m:
            city = c_m.group(1).strip()
        if s_m:
            state = s_m.group(1).strip()

    if state and isinstance(state, str):
        state = re.sub(r"^(?:state\s*(?:is|:)?\s*)", "", state, flags=re.I).strip()
    if city and isinstance(city, str):
        city = re.sub(r"^(?:city\s*(?:is|:)?\s*)", "", city, flags=re.I).strip()

    # Reject non-location tokens like 'yes', 'no', numbers, or booleans
    c_final = (city.strip() if city and isinstance(city, str) else None)
    s_final = (state.strip() if state and isinstance(state, str) else None)
    if c_final and (c_final.lower() in INVALID_LOCATION_WORDS or c_final.isdigit()):
        c_final = None
    if s_final and (s_final.lower() in INVALID_LOCATION_WORDS or s_final.isdigit()):
        s_final = None

    return (c_final or None), (s_final or None)


def normalize_ut_location(city: str | None, state: str | None) -> tuple[str | None, str | None]:
    """If either city or state is a Union Territory (e.g. Delhi or Chandigarh),

    automatically map it to both city and state to satisfy completeness.
    """
    c_clean = city.strip().lower() if city and isinstance(city, str) else ""
    s_clean = state.strip().lower() if state and isinstance(state, str) else ""

    # If city is a known UT and state is not specified
    if c_clean in UNION_TERRITORIES and not state:
        standard_ut = UNION_TERRITORIES[c_clean]
        return (city if c_clean != "delhi" else standard_ut), standard_ut

    # If state is a known UT and city is not specified
    if s_clean in UNION_TERRITORIES and not city:
        standard_ut = UNION_TERRITORIES[s_clean]
        return standard_ut, standard_ut

    # If city is a UT and state is also a UT
    if c_clean in UNION_TERRITORIES and s_clean in UNION_TERRITORIES:
        return city, UNION_TERRITORIES[c_clean]

    return city, state


# All 28 Indian States mapped to standard proper casing
INDIAN_STATES: dict[str, str] = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
}


def resolve_indian_location(
    city: str | None, state: str | None
) -> tuple[str | None, str | None, str | None]:
    """Resolves Indian locations: parses natural language, maps Union Territories,

    identifies Indian states, and infers suggested_state from major Indian tech and rental hubs.
    Returns:
        (city, state, suggested_state)
    """
    clean_c, clean_s = clean_location_input(city, state)
    ut_c, ut_s = normalize_ut_location(clean_c, clean_s)

    res_c = ut_c
    res_s = ut_s
    sugg_s = None

    if res_c and (str(res_c).strip().lower() in INVALID_LOCATION_WORDS or str(res_c).strip().isdigit()):
        res_c = None
    if res_s and (str(res_s).strip().lower() in INVALID_LOCATION_WORDS or str(res_s).strip().isdigit()):
        res_s = None

    # Check if city is actually a state name (e.g. user entered "himachal pradesh")
    if res_c and isinstance(res_c, str):
        c_low = res_c.strip().lower()
        if c_low in INDIAN_STATES and not res_s:
            res_s = INDIAN_STATES[c_low]
            res_c = None

    # Standardize casing for recognized states
    if res_s and isinstance(res_s, str):
        s_low = res_s.strip().lower()
        if s_low in INDIAN_STATES:
            res_s = INDIAN_STATES[s_low]

    # If state is still missing, suggest from known major Indian cities
    if not res_s and res_c and isinstance(res_c, str):
        c_key = res_c.strip().lower()
        if c_key in MAJOR_INDIAN_CITIES_TO_STATE:
            sugg_s = MAJOR_INDIAN_CITIES_TO_STATE[c_key]

    return res_c, res_s, sugg_s


class CaseFacts(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    scope: Literal["residential_deposit", "other", "unknown"] = "unknown"
    state: Optional[str] = None
    city: Optional[str] = None
    suggested_state: Optional[str] = Field(
        default=None,
        description="Possible state inferred from city, only if reasonably confident; not user-confirmed",
    )
    deposit_amount_inr: Optional[int] = Field(default=None, ge=0)
    amount_returned_inr: Optional[int] = Field(default=None, ge=0)
    move_out_date: Optional[str] = None
    written_agreement_exists: Literal["yes", "no", "unknown"] = "unknown"
    payment_proof_exists: Literal["yes", "no", "unknown"] = "unknown"
    deduction_reason: Optional[str] = Field(
        default=None,
        description="Landlord's stated reason or excuse for withholding money (flexible string, e.g. business losses, painting, etc.)",
    )
    deduction_amount_inr: Optional[int] = Field(default=None, ge=0)
    other_details: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    inferred_details: list[str] = Field(
        default_factory=list,
        description="Reasonable inferences clearly labeled for user review, not established facts",
    )

    @model_validator(mode="before")
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            # Support legacy alias 'agreement_exists' -> 'written_agreement_exists'
            if "agreement_exists" in data and "written_agreement_exists" not in data:
                data["written_agreement_exists"] = data.pop("agreement_exists")

            # Clean natural language phrases, resolve UTs and infer suggested_state from major cities
            city = data.get("city")
            state = data.get("state")
            norm_city, norm_state, sugg_state = resolve_indian_location(city, state)
            data["city"] = norm_city
            data["state"] = norm_state
            if sugg_state and not data.get("suggested_state"):
                data["suggested_state"] = sugg_state

            # Auto-calculate returned or deduction amount if deposit and one component are known
            dep_amt = data.get("deposit_amount_inr")
            ret_amt = data.get("amount_returned_inr")
            ded_amt = data.get("deduction_amount_inr")
            if dep_amt is not None and ded_amt is not None and ret_amt is None:
                data["amount_returned_inr"] = max(0, dep_amt - ded_amt)
            elif dep_amt is not None and ret_amt is not None and ded_amt is None:
                data["deduction_amount_inr"] = max(0, dep_amt - ret_amt)

            # Automatically clear uncertainties for any fields that are now known
            raw_unc = data.get("uncertainties", [])
            if raw_unc:
                cleared_unc = []
                for u in raw_unc:
                    u_lower = u.lower()
                    # 1. Location (city / state)
                    if (norm_city or norm_state or sugg_state) and any(k in u_lower for k in ["location", "city", "state"]):
                        continue
                    # 2. Deposit Amount
                    if data.get("deposit_amount_inr") is not None and any(k in u_lower for k in ["deposit", "security deposit"]):
                        continue
                    # 3. Amount Returned
                    if data.get("amount_returned_inr") is not None and any(k in u_lower for k in ["returned", "refund"]):
                        continue
                    # 4. Move-out Date
                    if data.get("move_out_date") and any(k in u_lower for k in ["move out", "move-out", "vacat", "date", "year"]):
                        continue
                    # 5. Written Agreement
                    if data.get("written_agreement_exists") in ("yes", "no") and any(k in u_lower for k in ["agreement", "lease", "contract"]):
                        continue
                    # 6. Payment Proof
                    if data.get("payment_proof_exists") in ("yes", "no") and any(k in u_lower for k in ["proof", "receipt"]):
                        continue
                    # 7. Deduction Reason
                    if data.get("deduction_reason") and any(k in u_lower for k in ["deduction reason", "reason for deduction", "withholding reason", "why landlord"]):
                        continue
                    # 8. Deduction Amount
                    if data.get("deduction_amount_inr") is not None and any(k in u_lower for k in ["deduction amount", "amount deducted", "withheld amount"]):
                        continue
                    cleared_unc.append(u)
                data["uncertainties"] = cleared_unc
        return data

    @property
    def agreement_exists(self) -> Literal["yes", "no", "unknown"]:
        return self.written_agreement_exists

    @agreement_exists.setter
    def agreement_exists(self, val: Literal["yes", "no", "unknown"]) -> None:
        self.written_agreement_exists = val
