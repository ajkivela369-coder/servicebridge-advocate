import unittest

from servicebridge.redaction import contains_unredacted_high_risk_identifier, redact_text


class RedactionTests(unittest.TestCase):
    def test_redacts_common_identifiers(self):
        text = "DOB: 01/02/1980; SSN 123-45-6789; email person@example.test; phone (202) 555-0183"
        redacted, counts = redact_text(text)
        self.assertNotIn("01/02/1980", redacted)
        self.assertNotIn("123-45-6789", redacted)
        self.assertNotIn("person@example.test", redacted)
        self.assertNotIn("202", redacted)
        self.assertEqual(counts["dob_label"], 1)
        self.assertEqual(counts["ssn"], 1)
        self.assertFalse(contains_unredacted_high_risk_identifier(redacted))

    def test_redaction_is_not_claimed_as_full_deidentification(self):
        redacted, counts = redact_text("The claimant's favorite color is green.")
        self.assertEqual(redacted, "The claimant's favorite color is green.")
        self.assertEqual(counts, {})


if __name__ == "__main__":
    unittest.main()