"""Invariants of the reference control catalog (`llmsafety.register`)."""
from __future__ import annotations

import re
import unittest

from dataclasses import replace

from llmsafety.register import (
    ASI_THREATS,
    CAPTURE_MODES,
    CATEGORIES,
    CATEGORY_LABELS,
    CONTROL_LAYERS,
    DECLARABLE_THREAT_STATUSES,
    EVIDENCE_CLASSES,
    REFERENCE_CONTROLS,
    REFERENCE_THREAT_POSTURE,
    controls_for,
    coverage,
    find_control,
    threat_coverage,
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


class TestThreatCoverage(unittest.TestCase):
    """Absent is never zero, one level up: a threat with no controls must say
    whether it is a gap or cannot apply."""

    def test_every_asi_id_used_is_a_known_threat(self):
        for c in REFERENCE_CONTROLS:
            if c.asi:
                self.assertIn(c.asi, ASI_THREATS)

    def test_control_names_its_threat_exactly_as_asi_threats_does(self):
        # asi_name is redundant with ASI_THREATS by design — it keeps a row
        # readable on its own. Redundant data drifts unless something forbids
        # it, and a control that renames its own threat is a crosswalk that
        # quietly stops reconciling with the published taxonomy.
        for c in REFERENCE_CONTROLS:
            if c.asi:
                self.assertEqual(c.asi_name, ASI_THREATS[c.asi], f"{c.id} renames {c.asi}")

    def test_no_threat_left_undeclared(self):
        self.assertEqual(threat_coverage().undeclared, [])

    def test_postures_name_a_known_threat_a_declarable_status_and_a_reason(self):
        for p in REFERENCE_THREAT_POSTURE:
            self.assertIn(p.threat, ASI_THREATS)
            self.assertIn(p.status, DECLARABLE_THREAT_STATUSES)
            self.assertTrue(p.reason, f"{p.threat} declares no reason")

    def test_no_posture_for_a_threat_controls_already_cover(self):
        covered = {c.asi for c in REFERENCE_CONTROLS if c.asi}
        for p in REFERENCE_THREAT_POSTURE:
            self.assertNotIn(p.threat, covered, f"{p.threat} is both covered and declared")

    def test_statuses_partition_the_whole_threat_list(self):
        tc = threat_coverage()
        self.assertEqual(tc.total, len(ASI_THREATS))
        self.assertEqual(
            len(tc.covered) + len(tc.gaps) + len(tc.not_applicable) + len(tc.undeclared),
            tc.total,
        )

    def test_reference_catalog_covers_seven_of_ten(self):
        tc = threat_coverage()
        self.assertEqual(len(tc.covered), 7)
        self.assertEqual(tc.gaps, ["ASI04"])
        self.assertEqual(tc.not_applicable, ["ASI07", "ASI10"])

    def test_reason_on_every_absence_and_on_no_coverage(self):
        for r in threat_coverage().rows:
            if r.status == "covered":
                self.assertIsNone(r.reason)
                self.assertTrue(r.controls)
            else:
                self.assertTrue(r.reason, f"{r.threat} is absent with no reason")
                self.assertEqual(r.controls, [])

    def test_derived_coverage_wins_over_a_stale_posture(self):
        # A control is added for ASI07 but the not-applicable posture is left
        # behind: the threat must read as covered, never suppressed by the
        # stale declaration.
        with_inter_agent = (*REFERENCE_CONTROLS, replace(REFERENCE_CONTROLS[0], id="AL-99", asi="ASI07"))
        tc = threat_coverage(with_inter_agent, REFERENCE_THREAT_POSTURE)
        self.assertIn("ASI07", tc.covered)
        self.assertNotIn("ASI07", tc.not_applicable)

    def test_empty_register_declares_nothing_and_hides_nothing(self):
        tc = threat_coverage([], [])
        self.assertEqual(len(tc.undeclared), len(ASI_THREATS))
        self.assertEqual(tc.covered, [])


if __name__ == "__main__":
    unittest.main()
