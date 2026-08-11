import { describe, expect, test } from "bun:test";
import {
  ASI_THREATS,
  CATEGORIES,
  CATEGORY_LABELS,
  REFERENCE_CONTROLS,
  REFERENCE_THREAT_POSTURE,
  controlsFor,
  coverage,
  findControl,
  threatCoverage,
} from "../src/register.ts";

describe("reference catalog invariants", () => {
  test("ids are unique and well-formed", () => {
    const ids = REFERENCE_CONTROLS.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const id of ids) expect(id).toMatch(/^[A-Z]{2}-\d{2}$/);
  });

  test("every control carries both audiences: plain and claim", () => {
    for (const c of REFERENCE_CONTROLS) {
      expect(c.plain.length).toBeGreaterThan(0);
      expect(c.claim.length).toBeGreaterThan(0);
    }
  });

  test("categories, evidence, capture and layer are all valid enum values", () => {
    const evidence = ["attestation", "detective", "test"];
    const capture = ["event", "private-note", "derived", "config", "not-instrumented"];
    const layer = ["trained", "prompt", "screening", "authorization", "platform"];
    for (const c of REFERENCE_CONTROLS) {
      expect(CATEGORIES).toContain(c.category);
      expect(evidence).toContain(c.evidence);
      expect(capture).toContain(c.capture);
      expect(layer).toContain(c.layer);
    }
  });

  test("ASI ids are well-formed and always named", () => {
    for (const c of REFERENCE_CONTROLS) {
      if (c.asi) {
        expect(c.asi).toMatch(/^ASI\d{2}$/);
        expect(c.asiName ?? "").not.toBe("");
      } else {
        expect(c.asiName).toBeUndefined();
      }
    }
  });

  test("a not-instrumented control always declares its gap", () => {
    for (const c of REFERENCE_CONTROLS) {
      if (c.capture === "not-instrumented") {
        expect((c.gap ?? "").length).toBeGreaterThan(0);
      }
    }
  });

  test("deployment-owned state ships empty in the reference catalog", () => {
    for (const c of REFERENCE_CONTROLS) {
      expect(c.source).toBeUndefined();
      expect(c.failing).toBeUndefined();
      expect(c.verifiedBy).toBeUndefined();
      expect(c.verifiedHow).toBeUndefined();
    }
  });

  test("every category label exists and every category has controls", () => {
    for (const cat of CATEGORIES) {
      expect(CATEGORY_LABELS[cat].length).toBeGreaterThan(0);
      expect(controlsFor(cat).length).toBeGreaterThan(0);
    }
  });
});

describe("helpers", () => {
  test("findControl returns the row or undefined", () => {
    expect(findControl("AL-01")?.category).toBe("alignment");
    expect(findControl("ZZ-99")).toBeUndefined();
  });

  test("coverage sums to the total across every axis", () => {
    const cov = coverage();
    expect(cov.total).toBe(REFERENCE_CONTROLS.length);
    const sum = (rec: Record<string, number>) => Object.values(rec).reduce((a, b) => a + b, 0);
    expect(sum(cov.byEvidence)).toBe(cov.total);
    expect(sum(cov.byCapture)).toBe(cov.total);
    expect(sum(cov.byLayer)).toBe(cov.total);
    expect(cov.notInstrumented.length).toBe(cov.byCapture["not-instrumented"]);
    expect(cov.failing).toEqual([]);
  });

  test("coverage works on an adopted subset", () => {
    const mine = REFERENCE_CONTROLS.slice(0, 5).map((c) => ({ ...c, source: "src/guards.ts" }));
    expect(coverage(mine).total).toBe(5);
  });
});

describe("threat coverage — absent is never zero, one level up", () => {
  test("every ASI id used by a control is a known threat", () => {
    for (const c of REFERENCE_CONTROLS) {
      if (c.asi) expect(Object.keys(ASI_THREATS)).toContain(c.asi);
    }
  });

  test("a control names its threat exactly as ASI_THREATS does", () => {
    // asiName is redundant with ASI_THREATS by design — it keeps a row readable
    // on its own. Redundant data drifts unless something forbids it, and a
    // control that renames its own threat is a crosswalk that quietly stops
    // reconciling with the published taxonomy.
    for (const c of REFERENCE_CONTROLS) {
      if (c.asi) expect(c.asiName).toBe(ASI_THREATS[c.asi]);
    }
  });

  test("no threat is left undeclared: every one is covered, a gap, or not applicable", () => {
    expect(threatCoverage().undeclared).toEqual([]);
  });

  test("every declared posture names a known threat, a declarable status, and a reason", () => {
    for (const p of REFERENCE_THREAT_POSTURE) {
      expect(Object.keys(ASI_THREATS)).toContain(p.threat);
      expect(["gap", "not-applicable"]).toContain(p.status);
      expect(p.reason.length).toBeGreaterThan(0);
    }
  });

  test("a posture is never declared for a threat controls already cover", () => {
    const covered = new Set(REFERENCE_CONTROLS.map((c) => c.asi).filter(Boolean));
    for (const p of REFERENCE_THREAT_POSTURE) expect(covered.has(p.threat)).toBe(false);
  });

  test("the four statuses partition the whole threat list", () => {
    const tc = threatCoverage();
    expect(tc.total).toBe(Object.keys(ASI_THREATS).length);
    expect(tc.covered.length + tc.gaps.length + tc.notApplicable.length + tc.undeclared.length).toBe(
      tc.total,
    );
  });

  test("the reference catalog covers 7 of 10, with one gap and two not applicable", () => {
    const tc = threatCoverage();
    expect(tc.covered.length).toBe(7);
    expect(tc.gaps).toEqual(["ASI04"]);
    expect(tc.notApplicable).toEqual(["ASI07", "ASI10"]);
  });

  test("a reason is carried on every absence and on no coverage", () => {
    for (const r of threatCoverage().rows) {
      if (r.status === "covered") {
        expect(r.reason).toBeUndefined();
        expect(r.controls.length).toBeGreaterThan(0);
      } else {
        expect(r.reason ?? "").not.toBe("");
        expect(r.controls).toEqual([]);
      }
    }
  });

  test("derived coverage wins over a stale posture", () => {
    // A control is added for ASI07 but the not-applicable posture is left behind:
    // the threat must read as covered, never suppressed by the stale declaration.
    const withInterAgent = [...REFERENCE_CONTROLS, { ...REFERENCE_CONTROLS[0]!, id: "AL-99", asi: "ASI07" }];
    const tc = threatCoverage(withInterAgent, REFERENCE_THREAT_POSTURE);
    expect(tc.covered).toContain("ASI07");
    expect(tc.notApplicable).not.toContain("ASI07");
  });

  test("an empty register declares nothing and hides nothing", () => {
    const tc = threatCoverage([], []);
    expect(tc.undeclared.length).toBe(Object.keys(ASI_THREATS).length);
    expect(tc.covered).toEqual([]);
  });
});
