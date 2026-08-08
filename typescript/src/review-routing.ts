/**
 * Review routing — route by confidence, reversibility, and cost.
 * Experimental (0.1.0).
 */
import type { CheckResult } from "./result.js";

export const status = "experimental" as const;

export type Route = "auto" | "human" | "senior";

/**
 * Return `"auto"`, `"human"`, or `"senior"` for a decision.
 * - senior: low confidence, or irreversible AND high cost
 * - human: medium confidence, or costs real money/time, or irreversible
 * - auto: high confidence, reversible, low cost
 */
export function route(confidence: number, reversible: boolean, highCost: boolean): Route {
  if (confidence < 0.5 || (!reversible && highCost)) return "senior";
  if (confidence < 0.8 || highCost || !reversible) return "human";
  return "auto";
}

/** Audit review-routing. Needs decision metadata (confidence/reversibility/cost) — planned. */
export function check(_response: string): CheckResult {
  return {
    domain: "review-routing",
    passed: null,
    score: null,
    findings: ["needs decision metadata (confidence/reversibility/cost); not scored from a response (0.1.0)"],
  };
}
