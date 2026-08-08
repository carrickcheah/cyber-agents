import { describe, expect, test } from "bun:test";
import {
  CATEGORIES,
  CATEGORY_LABELS,
  REFERENCE_CONTROLS,
  controlsFor,
  coverage,
  findControl,
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
