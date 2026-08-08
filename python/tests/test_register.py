"""Invariants of the reference control catalog (`aisafety.register`)."""
from __future__ import annotations

import re
import unittest

from aisafety.register import (
    CAPTURE_MODES,
    CATEGORIES,
    CATEGORY_LABELS,
    CONTROL_LAYERS,
    EVIDENCE_CLASSES,
    REFERENCE_CONTROLS,
    controls_for,
    coverage,
    find_control,
)


class TestReferenceCatalog(unittest.TestCase):
    def test_ids_unique_and_well_formed(self):
        ids = [c.id for c in REFERENCE_CONTROLS]
        self.assertEqual(len(set(ids)), len(ids))
        for control_id in ids:
            self.assertRegex(control_id, r"^[A-Z]{2}-\d{2}$")

    def test_both_audiences_present(self):
        for c in REFERENCE_CONTROLS:
            self.assertTrue(c.plain)
            self.assertTrue(c.claim)

    def test_enum_values_valid(self):
        for c in REFERENCE_CONTROLS:
            self.assertIn(c.category, CATEGORIES)
            self.assertIn(c.evidence, EVIDENCE_CLASSES)
            self.assertIn(c.capture, CAPTURE_MODES)
            self.assertIn(c.layer, CONTROL_LAYERS)

    def test_asi_ids_well_formed_and_named(self):
        for c in REFERENCE_CONTROLS:
            if c.asi:
                self.assertTrue(re.fullmatch(r"ASI\d{2}", c.asi))
                self.assertTrue(c.asi_name)
            else:
                self.assertIsNone(c.asi_name)

    def test_not_instrumented_declares_gap(self):
        for c in REFERENCE_CONTROLS:
            if c.capture == "not-instrumented":
                self.assertTrue(c.gap, f"{c.id} is not-instrumented with no declared gap")

    def test_deployment_state_ships_empty(self):
        for c in REFERENCE_CONTROLS:
            self.assertIsNone(c.source)
            self.assertFalse(c.failing)
            self.assertIsNone(c.verified_by)
            self.assertIsNone(c.verified_how)

    def test_every_category_labelled_and_populated(self):
        for cat in CATEGORIES:
            self.assertTrue(CATEGORY_LABELS[cat])
            self.assertTrue(controls_for(cat))


class TestHelpers(unittest.TestCase):
    def test_find_control(self):
        found = find_control("AL-01")
        self.assertIsNotNone(found)
        self.assertEqual(found.category, "alignment")
        self.assertIsNone(find_control("ZZ-99"))

    def test_coverage_sums_to_total(self):
        cov = coverage()
        self.assertEqual(cov.total, len(REFERENCE_CONTROLS))
        self.assertEqual(sum(cov.by_evidence.values()), cov.total)
        self.assertEqual(sum(cov.by_capture.values()), cov.total)
        self.assertEqual(sum(cov.by_layer.values()), cov.total)
        self.assertEqual(len(cov.not_instrumented), cov.by_capture["not-instrumented"])
        self.assertEqual(cov.failing, [])

    def test_coverage_on_adopted_subset(self):
        subset = REFERENCE_CONTROLS[:5]
        self.assertEqual(coverage(subset).total, 5)


if __name__ == "__main__":
    unittest.main()
