/**
 * Fairness — make unequal outcomes measurable. Experimental (0.1.0).
 */
import type { CheckResult } from "./result.js";

export const status = "experimental" as const;

/** Best-effort language tag (`zh` / `ms` / `en` / `null`). A sample language
 * set — swap in the languages your own deployment serves. */
export function detectLanguage(text: string): "zh" | "ms" | "en" | null {
  if (!text) return null;
  if (/[一-鿿]/.test(text)) return "zh";
  if (/\b(saya|nak|boleh|tak|apa|berapa|macam|ada)\b/i.test(text)) return "ms";
  if (/[a-zA-Z]{2,}/.test(text)) return "en";
  return null;
}

/** Audit fairness. One response only reveals its language; real per-group
 * fairness needs many samples (planned). */
export function check(response: string): CheckResult {
  const lang = detectLanguage(response);
  return {
    domain: "fairness",
    passed: null,
    score: null,
    findings: [`response language=${lang}; per-language fairness needs multiple samples (0.1.0)`],
  };
}
