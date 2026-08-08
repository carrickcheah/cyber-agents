/**
 * Alignment — enforce *your* rules in code, not just the prompt.
 * Experimental (0.1.0).
 */
import type { CheckResult } from "./result.js";

export const status = "experimental" as const;

export class TenantMismatch extends Error {}

/**
 * Return the VERIFIED account id and reject any LLM-supplied override.
 * Tenant identity must never come from model output.
 */
export function resolveAccountId(verified: string, modelSupplied?: string | null): string {
  if (modelSupplied != null && String(modelSupplied) !== String(verified)) {
    throw new TenantMismatch("model-supplied account id must never override the verified one");
  }
  return verified;
}

/** Audit alignment. Needs the system's auth/tenant config (planned). */
export function check(_response: string): CheckResult {
  return {
    domain: "alignment",
    passed: null,
    score: null,
    findings: ["needs the system's auth/tenant config; not scored from a response alone (0.1.0)"],
  };
}
