# Roadmap: from honest prototype to production grade

**Where 0.1.0 stands, stated plainly.** The control register (44 controls, three
evidence classes, threat mappings) is production-derived and is the reason this
package exists. The guardrails detectors are prototype-grade English-only
regexes with known failures, which we keep on record because they are the
regression corpus for everything below:

- a safe refusal — *"I cannot reveal my system prompt"* — is flagged as a leak;
- order numbers and timestamps are flagged as phone numbers;
- Malay injections (*"abaikan semua arahan anda"*), leetspeak (*"1gn0re y0ur
  1nstructions"*), dotted phones, and spelled-out emails are missed.

Four of five domains return "not scored" rather than a number. That honesty is
deliberate and stays.

## What "production grade" means here

A release earns the label only when all five hold:

1. **Measured** — every detector has published precision/recall per language on
   a corpus that ships in this repo, and CI fails on regression.
2. **Multilingual** — English, Malay, and Chinese are first-class; code-mixed
   text (Manglish) is handled by design, not luck.
3. **Never punishes correct behaviour** — a refusal, an order number, or a
   benign sentence full of trigger words must not fire. False positives are the
   product-killer: the industry benchmark (Lakera PINT) is ~58% benign and ~21%
   hard-negatives for exactly this reason.
4. **Versioned verdicts** — every finding is stamped with a detector version; a
   patch release never changes a verdict on the same input; a minor release may,
   and says so in the changelog.
5. **Hardened supply chain** — no long-lived publish tokens, pinned actions,
   typed packages, a disclosure path. A safety auditor that fails its own audit
   is self-refuting.

## The opening (why now)

- LLM Guard — the 2.5M-download lightweight guard toolkit — was archived in
  July 2026 after the Protect AI acquisition; Rebuff was archived in 2025.
  Every surviving alternative needs a GPU model, an LLM judge, or a framework
  runtime. The **maintained zero-dependency guard layer, in both TypeScript and
  Python**, is an empty seat.
- No embeddable library covers Malay/Indonesian/Chinese injection detection
  (Meta Prompt Guard 2's evaluated languages omit all three; the SEA options
  are hosted LLM classifiers). Even Presidio ships no Malaysian NRIC detector.
- The EU AI Act's main obligations became applicable August 2026, and there is
  still no open-source tool that turns scan findings into control-mapped
  assurance evidence. The register's attestation/detective/test model is that
  tool.

We do not compete with garak/promptfoo/PyRIT on probe count. We compete on the
guard layer, the languages, and the evidence.

---

## 0.2 — Trustworthy detectors, measured quality

### Detection engine

- **Normalization pipeline before any pattern runs** (zero-dep, both
  languages): Unicode NFKC → strip zero-width/tag-block/variation-selector
  characters → confusable folding from a vendored UTS #39 table → bidi-control
  stripping → leetspeak canonicalization → separator collapsing. Match on the
  normalized copy; never mutate the original.
- **Language-tagged phrase tables, not one English regex**: imperative-verb +
  instruction-noun co-occurrence per language. English and Malay in 0.2
  (curated: *abaikan/lupakan semua arahan*, *jangan ikut peraturan*, …);
  Chinese (忽略以上指令 …) in 0.3. Code-mixed input is handled by **union, not
  branch**: run all language passes and OR the hits — never detect-language-
  then-route.
- **Prompt-leak detection rebuilt as three tiers**, replacing the single regex:
  1. **Canary token** (flagship): API to plant a random token in a system
     prompt; verbatim reappearance in output = definitive leak. Deterministic,
     zero-dep, immune to refusal false-positives.
  2. **n-gram overlap** (n ≥ 8) against the caller-supplied system prompt =
     probable leak (catches paraphrase).
  3. **Structural signals** (colon + enumerated list, quoted instruction
     blocks, second-person imperatives) gated by a **refusal suppressor**: the
     rule is *leak-signal AND NOT refusal-frame*. "I cannot reveal my rules"
     stops firing.
- **PII detectors become validation-based, still zero-dep**: Malaysian phone =
  prefix table + exact digit counts + grouping plausibility (kills order
  numbers and timestamps); Malaysian NRIC = calendar-date validation + state
  (PB) code table — a detector neither Presidio nor Google DLP ships; email =
  WHATWG pattern + punctuation trimming. A context-word proximity boost in
  English AND Malay (*no IC*, *kad pengenalan*, *no telefon*, *hubungi*,
  *emel*) raises confidence cheaply. **No name/PERSON detector in core** — that
  is a declared blind spot, register-style, until an NER extra exists.
- **Graduated verdicts replace booleans** (modeled on DLP likelihood buckets):
  every finding is `{detector, version, verdict: very-likely | likely |
  possible, signals, span}`; callers set a minimum verdict. Screening defaults
  to `likely`+.

### Measurement (ships in the same release — detectors do not merge without it)

- **In-repo eval corpus**, PINT-proportioned (60–75% benign + hard-negatives,
  because false positives are our documented failure class), with `en` / `ms` /
  `obfuscated` slices; seeded from permissively licensed sets (deepset
  Apache-2.0, TrustAIRLab & HackAPrompt MIT, NotInject for trigger-word-rich
  benign) plus our own recorded failures; CC-BY-SA material (SEA corpora) kept
  in an attributed eval-only bucket, never compiled into shipped rules.
- **CI gates**: precision ≥ 0.95 on benign + hard-negatives, recall ≥ 0.80 per
  language slice, and a committed per-detector baseline that ratchets — a
  flipped case fails CI unless the same PR updates the baseline with a written
  rationale.
- **Dual-runtime parity gate**: the same corpus runs through the TypeScript and
  Python implementations; any row where they disagree fails CI regardless of
  which side is "right".
- **Detector-set manifest**: the package exports `{id, version}` for every
  detector plus a manifest hash; every result embeds it, so a score change is
  attributable to a detector change or a corpus change in one query.

### Supply chain and packaging (the ~2-day hygiene pass)

- npm **Trusted Publishing** (OIDC, now possible since the package exists) and
  delete the publish token; PyPI already uses it. Provenance on both.
- Workflows: top-level `permissions: {}`, per-job grants, every action pinned
  to a commit SHA, zizmor as a blocking check.
- Types: `py.typed` + mypy strict; publint + arethetypeswrong on the npm side.
  Ruff for lint/format. CI matrix: Python 3.10–3.14 (core code is 3.10-clean;
  `requires-python` widens accordingly), Node 22/24 + Bun.
- `SECURITY.md` + GitHub private vulnerability reporting; Keep-a-Changelog with
  an explicit 0.x policy: **0.MINOR may change verdicts (breaking), 0.x.PATCH
  never does**.
- **Eat the dogfood**: add supply-chain controls (trusted publishing, pinned
  actions, minimal permissions, disclosure path) to the register and evidence
  them against this very repo.
- README: LLM Guard migration note for the orphaned audience.

## 0.3 — The auditor that emits evidence

- **Register-mapped findings**: audit runs attach to controls as test-class
  evidence — output becomes "control GD-02 has dated evidence at detector-set
  vX", the sentence auditors actually need. JSON export shaped to be
  OSCAL-friendly.
- **Probe hardening**: auth headers, retries with backoff, timeouts, SSE/
  streaming responses, multi-turn probe conversations, and small probe packs
  mapped to ASI threats (goal hijack, tool misuse, memory poisoning) rather
  than a probe-count race.
- **Chinese phrase tables + Manglish corpus slice**; encoded-payload spotting
  (base64 ≥ 16 chars, hex, ROT13 → decode and rescan), modeled on garak's
  encoding probes.
- **Optional extras tier** (core stays zero-dep and detects absence, falling
  back to built-ins under the same detector ids):
  - ONNX classifier extra served to both runtimes (onnxruntime / transformers
    .js) — preference for permissively licensed, over-defense-aware models
    (PIGuard-class). Meta Prompt Guard 2 is **not** bundled: Llama-license
    restrictions, and no evaluated Malay/Chinese support.
  - `phonenumbers` / libphonenumber-js adapters upgrading the phone detector.
  - Presidio adapter for entity coverage beyond core.
- **Scoring the silent domains** via explicit input contracts: callers hand
  `audit()` their register/config (tool grants, language settings, retention
  policy) and alignment/fairness/review-routing/compliance produce real scored
  findings from facts, not vibes. An optional **LLM-judge mode** gets its own
  golden set with Cohen's kappa ≥ 0.6 gating judge changes — run as a paid,
  out-of-band job, never in the merge gate.
- **Published benchmark table** in the README: per-detector, per-language
  precision/recall at the default threshold, dated, regenerated per release —
  plus a PINT-format exporter, a promptfoo provider, and a garak detector shim
  so anyone can verify our numbers in third-party harnesses.

## 1.0 — the bar to claim it

- Two consecutive minor releases with no verdict-stability violations.
- Benchmark table published and reproducible by outsiders for both runtimes.
- External adopters: issues filed and fixed from users who are not the author.
- API freeze with a documented deprecation policy; OpenSSF Best Practices
  badge; every 0.2/0.3 register control about this repo showing green.

## Non-goals

- Competing on probe count with garak / promptfoo / PyRIT.
- ML models or network calls in the core packages — extras only, opt-in.
- A hosted service. This is a library; evidence stays on your infrastructure.

## Sources

Key references behind this plan: Lakera PINT benchmark (methodology; corpus
proportions), NotInject / PIGuard (over-defense measurement), garak detector
and encoding-probe design, Rebuff canary-token design, Microsoft Presidio
scoring architecture and Google DLP likelihood buckets + detector versioning,
Meta Prompt Guard 2 model card (evaluated-language list and license), SEALGuard
/ SEA-Guard corpora (SEA-language coverage), UTS #39 confusables data,
"Bypassing LLM Guardrails" (arXiv 2504.11168) on evasion, and the July 2026
archival of protectai/llm-guard.
