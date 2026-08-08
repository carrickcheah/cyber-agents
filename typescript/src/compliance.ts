/**
 * Compliance — pin each obligation to a control, an owner, and evidence.
 * Experimental (0.1.0).
 */
import type { CheckResult } from "./result.js";

export const status = "experimental" as const;

/** One row of a data-protection controls register. */
export interface Control {
  obligation: string;
  control: string;
  owner: string;
  evidence: string;
}

export function control(obligation: string, control: string, owner: string, evidence: string): Control {
  return { obligation, control, owner, evidence };
}

/** Audit compliance. Mapping obligations → controls → evidence needs the
 * system's register/config, not a single response (planned). */
export function check(_response: string): CheckResult {
  return {
    domain: "compliance",
    passed: null,
    score: null,
    findings: ["needs the system's controls register/config; not scored from a response (0.1.0)"],
  };
}
