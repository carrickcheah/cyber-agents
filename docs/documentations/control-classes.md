# Control classes — the 0.2 API surface

> **Status: PROPOSED — design approved 2026-08-11, not yet implemented.**
> Nothing in this document ships in `0.1.0`. This is the agreed shape for the
> next release. When a class lands, move its row's status by removing this
> banner section for the shipped parts — the doc must never claim more than
> the code does.

Every row of the 44-control reference catalog gets a runnable counterpart:
`from llmsafety import alignment` → `alignment.RefundBlocked()`. Class names
follow the control's short label, **three English words maximum**, PascalCase.
The reference catalog thereby becomes 44 ready-made shortcuts over ~12 generic
patterns underneath — a contact centre uses the named class as-is; every other
system uses the generic pattern with its own parameters:

```python
lock = alignment.RefundBlocked()                                   # catalog defaults
lock = alignment.ToolBlocked(denied=["wire_transfer"], control="AL-01")   # a bank
```

## Three kinds of class

Not every control lives in the request path, so the classes come in three
kinds — and the three kinds are the three evidence classes, as code:

| Kind | What it does | Runs when | Evidence it produces |
|---|---|---|---|
| **guard** | raises — the action dies | in the user's code path | detective (fired events) |
| **detector** | detects + records; the user decides what to do | in the user's code path | detective (fired events) |
| **attest** | checks a config or state is true | at `llmsafety audit` time | attestation |

Guards and detectors emit an evidence event on every fire (see the evidence
design below). Attest classes take a `check=` callable and are executed by the
audit, never in the request path.

## Alignment (9)

| ID | Class | Kind | Underneath |
|---|---|---|---|
| AL-01 | `alignment.RefundBlocked()` | guard | `ToolBlocked(denied=..., family=r"refund\|return")` |
| AL-02 | `alignment.BuiltinsDenied()` | guard | `ToolBlocked(family=r"shell\|file\|fetch")` |
| AL-03 | `alignment.EmptyRunEscalates()` | detector | empty output → escalate to human |
| AL-04 | `alignment.ErrorHidden()` | guard | provider error text never reaches customer |
| AL-05 | `alignment.PromiseDetected()` | detector | `PromiseDetector(promises=[r"refund", ...])` |
| AL-06 | `alignment.DenyByDefault()` | guard | allowlist gate — zero tools unless granted |
| AL-07 | `alignment.SealedWorkspace()` | attest | session isolation config is on |
| AL-08 | `alignment.NoRetry()` | guard | side-effect guard — never send twice |
| AL-09 | `alignment.DeliveryConfirmed()` | detector | send failed → retry loop + record |

## Guardrails (13)

Voice-channel controls (`VC-*`) are filed here, as in the catalog.

| ID | Class | Kind | Underneath |
|---|---|---|---|
| GD-01 | `guardrails.SenderRateLimit()` | guard | per-sender flood cap |
| GD-02 | `guardrails.InjectionDetected()` | detector | hijack phrasing tagger (ships today as `looks_like_injection`) |
| GD-03 | `guardrails.EvidenceRequired()` | guard | no retrieval proof → no answer, hand to human |
| GD-04 | `guardrails.InboundCap()` | guard | long message cut (ships today as `cap_text`) |
| GD-05 | `guardrails.LoopBreaker()` | guard | bot replying to itself → stop |
| GD-06 | `guardrails.TurnCap()` | guard | one question cannot run forever |
| GD-07 | `guardrails.HourlyReplyCap()` | guard | replies per chat per hour |
| GD-08 | `guardrails.EchoGuard()` | guard | reply copy can never wake the bot |
| GD-09 | `guardrails.StaffReplyGuard()` | guard | bot never answers your own staff |
| VC-01 | `guardrails.VoiceReplyGuard()` | guard | every spoken reply checked before heard |
| VC-02 | `guardrails.VoiceCanary()` | detector | risky spoken reply flagged, never blocked |
| VC-03 | `guardrails.WalletGate()` | guard | no balance → number does not answer |
| VC-04 | `guardrails.HandoverFlip()` | guard | handover moves the call to staff |

## Fairness (5)

| ID | Class | Kind | Underneath |
|---|---|---|---|
| FA-01 | `fairness.SameKit()` | attest | one shared instruction kit, no per-customer variants |
| FA-02 | `fairness.NoVipLane()` | attest | same bot for everyone, no priority path |
| FA-03 | `fairness.AnyLanguage()` | attest | same service in any language |
| FA-04 | `fairness.LimitsVisible()` | attest | language limits are a visible setting |
| FA-05 | `fairness.DeliberateBlock()` | detector | only staff can block a customer — each block recorded |

## Review routing (7)

RR-06 and RR-08 stay absent — numbering gaps are audit leads, in the API as in
the catalog.

| ID | Class | Kind | Underneath |
|---|---|---|---|
| RR-01 | `review_routing.HandoverInCode()` | guard | code hands over, never the model's choice |
| RR-02 | `review_routing.RecheckBeforeSend()` | guard | staff replied first → bot reply dropped |
| RR-03 | `review_routing.OneHandover()` | attest | one open handover per chat, max |
| RR-04 | `review_routing.FailedMuteSurfaced()` | detector | bot fails to go quiet → alarm |
| RR-05 | `review_routing.OneAlert()` | attest | one alert per chat, not per message |
| RR-07 | `review_routing.HandoverSla()` | detector | customer waiting too long → alert |
| RR-09 | `review_routing.HandoverAutoReset()` | attest | idle chat returns to the bot |

## Compliance (10)

CP-04 stays absent, as in the catalog.

| ID | Class | Kind | Underneath |
|---|---|---|---|
| CP-01 | `compliance.MemoryRetention()` | attest | old chat memory deleted on schedule |
| CP-02 | `compliance.BackupsEncrypted()` | attest | backup encryption is on |
| CP-03 | `compliance.PhoneMasked()` | attest | logs show last digits only |
| CP-05 | `compliance.AdminTwoFactor()` | attest | admin login needs second factor |
| CP-06 | `compliance.OneSession()` | attest | new device signs out the old |
| CP-07 | `compliance.NotesInternal()` | guard | staff notes never reach customer or bot |
| CP-08 | `compliance.BackupsChecked()` | attest | backups tested, old ones pruned |
| CP-09 | `compliance.AdminOnly()` | attest | billing/settings behind admin role |
| CP-10 | `compliance.JobsRun()` | detector | a job that stops firing shows up |
| CP-11 | `compliance.CriticalPaged()` | attest | critical events reach a real person |

## How an attest class works

Nothing in the request path — the user hands it a way to check, and
`llmsafety audit` runs it:

```python
# llmsafety: CP-02
compliance.BackupsEncrypted(
    check=lambda: read_backup_config().encryption == "on"
)
# audit time → runs check() → PASS/FAIL into the evidence file
```

## How Enforceability | Observability | Auditability appear in user code

```python
from llmsafety import alignment, evidence

# llmsafety: AL-01
refund_lock = alignment.RefundBlocked()

def on_tool_call(tool, args):        # the user's own hook — we never own the path
    refund_lock.check(tool)          # Enforceability: raises, tool never runs
                                     # Observability: fire event written automatically
```

- **Enforceability** — the helper raises in the user's code path. Their wiring,
  our function. The rule is in code, not in the prompt.
- **Observability** — every fire appends one JSON line to a local
  `llmsafety-evidence.jsonl`. No OpenTelemetry, no Langfuse, no server
  required; external sinks are an optional one-line adapter, never a
  dependency. `evidence.fired("AL-01", days=30)` answers "did it fire?".
- **Auditability** — `llmsafety audit` (read-only, run by the user, on their
  machine) connects register + `# llmsafety: <ID>` markers + evidence log +
  proof tests into a dated report: terminal table for the developer,
  `--json` evidence artifact for the archive, `--html` one-file safety page
  for the auditor. Exit non-zero on a broken claim gates CI.

The helpers are optional. A user who keeps their own enforcement adds the
marker and one `evidence.fire("AL-01")` line, and all three properties still
hold — llmsafety never demands to be the enforcer, only to be able to prove
the enforcer exists, fires, and stays proven.

## Totals

**44 classes: 20 guard · 9 detector · 15 attest.**
