"""Unit tests for One-Click Court Dossier Compiler."""

import unittest
from models import CaseFacts
from dossier import compile_court_dossier


class DossierCompilerTests(unittest.TestCase):
    def test_contested_unjustified_dossier_structure(self):
        """Contested dossier must contain Synopsis, Statutory Grounds, Prayer, and Index of Annexures."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=30000,
            amount_returned_inr=15000,
            deduction_amount_inr=15000,
            deduction_reason="painting and cleaning",
            move_out_date="2024-04-30",
            city="Delhi",
            state="Delhi",
        )
        dossier = compile_court_dossier(case)
        self.assertIn("PRE-LITIGATION CASE DOSSIER", dossier)
        self.assertIn("SYNOPSIS & LIST OF DATES AND EVENTS", dossier)
        self.assertIn("Section 73, Indian Contract Act, 1872", dossier)
        self.assertIn("Section 11, Model Tenancy Act, 2021", dossier)
        self.assertIn("PRAYER & RELIEF SOUGHT", dossier)
        self.assertIn("INDEX OF ANNEXURES (FILING CHECKLIST)", dossier)
        self.assertIn("Annexure C-1", dossier)
        self.assertIn("Annexure C-2", dossier)
        self.assertIn("₹15,000", dossier)

    def test_justified_invoiced_dossier_generates_discharge_record(self):
        """When posture is justified, compiler generates mutual settlement discharge instead of adversarial petition."""
        case = CaseFacts(
            scope="residential_deposit",
            deposit_amount_inr=80000,
            amount_returned_inr=50000,
            deduction_amount_inr=30000,
            deduction_reason="glass door replacement with contractor GST invoice",
            other_details=["landlord provided GST tax invoice and utility bill for broken door"],
            city="Bengaluru",
            state="Karnataka",
        )
        dossier = compile_court_dossier(case, posture="justified")
        self.assertIn("TENANCY DISCHARGE & MUTUAL SETTLEMENT DOSSIER", dossier)
        self.assertIn("Accord & Satisfaction", dossier)
        self.assertIn("Annexure S-1", dossier)
        self.assertIn("Annexure S-3", dossier)
        self.assertNotIn("PRE-LITIGATION CASE DOSSIER", dossier)


if __name__ == "__main__":
    unittest.main()

