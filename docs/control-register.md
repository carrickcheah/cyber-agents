# The control register pattern

A **safety control register** is the spine of an auditable AI system: one typed
list, in shipped source code, where every guardrail is a row an auditor can
walk — what you claim, how it is proven, where it lives. This document is the
pattern; [`control-catalog.md`](control-catalog.md) is the 44-control reference
catalog that ships as data in `aisafety/register` (TS) and
`aisafety.register` (Python).

Everything here was extracted from a production multi-tenant AI contact centre
— these are the rules that survived real audits and real incidents, not theory.

## Why the register lives in `src/`, not in a document

A real audit found the claim *"a written guardrail inventory is kept in the
repo and updated together with the system it describes"* to be false: the
inventory lived in a gitignored docs folder. Moving the register into shipped
source makes the claim true **by construction**:

- it moves with the code and cannot drift without a diff,
- it is reviewed in the same PRs that change the controls,
- the safety dashboard and the audit report are *generated from it*, so the
  page cannot say something the code does not.

The standing rule that keeps it honest: **no guardrail ships without an
auditable record.** Every new control lands with a register entry, an evidence
class, and *either* an event kind *or* an explicit declared gap. Declaring a
gap is acceptable; leaving one undeclared is not — a caveat living only in a
commit message is exactly the unverifiable claim the register replaces.

## The schema, field by field

```ts
interface SafetyControl {
  id: string;                 // "AL-01" — stable, never reused
  category: SafetyCategory;   // alignment | guardrails | fairness | review-routing | compliance
  shortLabel?: string;        // 2–3 words. NOT `label` — see below
  plain: string;              // the control in the operator's words, ~7 words, no jargon
  claim: string;              // what you assert to an auditor — falsifiable
  evidence: EvidenceClass;    // attestation | detective | test
  capture: CaptureMode;       // event | private-note | derived | config | not-instrumented
  layer: ControlLayer;        // trained | prompt | screening | authorization | platform
  owasp?: string;             // LLM Top 10 id
  asi?: string;               // OWASP Agentic Security Initiative threat id
  asiName?: string;           // human name of the ASI threat, e.g. "Tool Misuse"
  asiWhy?: string;            // one line: why this control maps to that threat
  notes?: string;             // design lessons and declared limits carried with the control
  gap?: string;               // what is missing — required when capture is not-instrumented
  // deployment-owned — empty in the reference catalog, yours to fill:
  source?: string;            // where it is implemented in YOUR codebase
  failing?: boolean;          // KNOWN broken right now (reason in gap)
  verifiedBy?: VerifiedBy;    // mutation | prod-read | unproven
  verifiedHow?: string;       // what was run, so a reader can repeat it
}
```

**Two audiences, two sentences.** `claim` is written for an auditor as a
falsifiable statement. `plain` is the same control for the person who runs the
business — required, not optional, because an empty plain cell renders as
"this one does nothing".

**Claims must be honest about detection vs prevention.** One control was
reworded from *"the bot never promises X"* to *"a first-person X promise is
detected and recorded"*, because the code was log-only observation; prevention
was a different control's job. Claiming prevention where only detection exists
is the unverifiable claim the register removes.

**`shortLabel`, not `label`.** Rendering pipelines commonly overwrite a `label`
key with the category label; a control-level `label` gets silently clobbered on
the way to the page.

**Status is computed, never stored.** There is deliberately no `status` field.
A control's live status is derived per request from evidence — a hardcoded
status is exactly the unverifiable claim the register exists to replace.

## Three evidence classes — not interchangeable

SOC 2 makes the same split between test-of-design and
test-of-operating-effectiveness:

| Class | Question it answers | Typical source |
|---|---|---|
| **attestation** | is the control configured ON, right now? | live config reads, 2FA enrollment, compile-time constants |
| **detective** | did it fire, and can you show the records? | durable guardrail events, prefixed private notes |
| **test** | how do you know it still works when it has *not* fired? | eval runs pushed to your own store |

A control that has never fired is indistinguishable from one that is switched
off — unless you hold all three apart. "Checked N, caught 0" is evidence;
a bare zero is not: **count the looking, not just the catching.**

## Absent is never zero

`not-instrumented` is a first-class capture mode, and the binding UI rule is
that an uninstrumented control *says so* instead of rendering a reassuring
zero. The same principle at every layer:

- a gate with no scored items renders the words **GATE ABSENT**, never `1.000`
  — enforced in the *schema* (value NULL ⇔ denominator zero) so no renderer
  default can undo it;
- a scheduled job that has never reported renders **never-run**, not a blank;
- an attestation that cannot see its control returns **not-observable** with
  the reason, never a green tick;
- "latest" means latest **attempt**, not latest success — a broken run
  displaces a previous pass in the headline.

## The `failing` flag

A prose "CURRENTLY FAILING" in a notes field is invisible to a renderer: in the
originating system a known-broken control sat grouped with healthy ones for
weeks, reading as an all-clear. A declared failure must outrank every other
cell state **except** a live attestation that can see the control — live truth
wins, so fixing the thing fixes the page. Keep a test that asserts `failing`
stays in step with the prose.

## Verification vocabulary

`verifiedBy` answers "is it actually working, or just described?":

- **mutation** — the control was deliberately broken in the shipped file and
  the test suite went red, then restored. Proves the test catches a real
  regression rather than passing vacuously. The strongest mode. Design the
  mutation so non-guarded paths still pass — proving it removed the *guard*,
  not the feature.
- **prod-read** — live state read from production. A snapshot, not a
  regression guard; a prod-read can also *fail*, which is recorded honestly.
- **unproven** — neither was possible. Stated explicitly rather than left to
  look equal to the verified rows.

One display rule: a dated prod-read snapshot sitting beside a live attestation
can contradict it, and an evidence page that contradicts itself teaches the
reader to trust neither — the live reading is authoritative; date the snapshot
as historical.

## Numbering gaps are audit leads

Ids are stable and never reused, so gaps in the sequence accumulate — and they
are worth questioning rather than trusting. In the originating system, chasing
numbering gaps uncovered real, shipped guardrails with no register entry, and
the worse variant: production emitting evidence against a control id the page
did not define, so real fires rendered nowhere. The reference catalog keeps its
original gaps (RR-06, RR-08, CP-04) for exactly this reason.

Two more register rules from the same audits:

- **Taxonomy over tidiness** — file a control in the category its threat family
  belongs to; never use it to fill a numbering gap elsewhere.
- **Register-first in both directions** — evidence for an unregistered control
  is as wrong as a register row with no evidence.

## Adopting it

1. Copy the reference catalog and delete the rows your system does not have.
   An honest 12-row register beats an aspirational 44-row one.
2. Fill the deployment-owned fields: `source` for every row; `gap` for
   everything not yet instrumented; `failing` for anything known broken.
3. Wire the three evidence classes: attestation reads, a fail-open event
   emitter for fires, eval results pushed to your own store.
4. Generate your safety page and your audit export *from the register*, so
   they cannot disagree with it.
5. Run a mutation pass: break each control on purpose, watch the suite go red,
   restore, record `verifiedBy`.

See [`design-principles.md`](design-principles.md) for the twenty cross-cutting
principles and the fifteen mechanism patterns (reply guard, grounding guard,
loop breaker, canary, evidence emitter, …) that back these controls.
