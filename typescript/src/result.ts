/** Outcome of auditing a system's response against one domain's metrics. */
export interface CheckResult {
  domain: string;
  /** `null` when there isn't enough signal yet / not implemented in this release. */
  passed: boolean | null;
  /** 0..1, or `null` when not scored. */
  score: number | null;
  findings: string[];
}
