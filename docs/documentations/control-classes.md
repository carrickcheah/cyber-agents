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

## Install

```bash
uv add llmsafety
```

Always `uv add`, never `uv pip install`. `uv add` records the dependency in
`pyproject.toml` and pins it in `uv.lock`, so `uv sync --locked` reproduces the
environment exactly and fails loudly if the lockfile has drifted.
`uv pip install` installs the package and writes nothing down — the next
machine has no way to know it was needed. That is this project's own principle
one layer out: an undeclared dependency is an unmeasured control.

For running the audit against a repository you do not own, `uvx llmsafety audit`
runs it without touching that project's dependencies at all.

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

## Four verbs

One verb per kind, so a reader never has to remember which class behaves how:

| Kind | Verb | Behaviour |
|---|---|---|
| guard | `.enforce(x)` | raises on violation — the action dies |
| detector | `.detect(x)` | returns findings — the caller decides |
| attest | `.verify()` | returns pass/fail + reason, at audit time |
| stateful guard | `.record(key)` | remembers what already happened |

**Guards raise rather than return** because a return value can be ignored, and
an ignored guard is a control that does nothing. Raising fails closed, which is
the deliberate failure direction a guard should have. Detectors are the
opposite on purpose: AL-05 catches the bot *promising* a refund, and the reply
may still need to send with a human alerted — so it reports and never raises.

`.record()` exists only on the stateful guards (AL-08, GD-01, GD-05, GD-06,
GD-07, RR-05), which must remember across calls. That memory is why controls
are classes rather than plain functions: a function forgets everything between
invocations. The class also carries its own control id, so `evidence.fire()`
can never be written against an id the register does not define — the AL-02
failure that the originating system hit in production.

Variable names are the user's own choice; only the class name and the verb are
API:

```python
lock   = alignment.RefundBlocked()   # same thing
guard  = alignment.RefundBlocked()   # same thing
refund = alignment.RefundBlocked()   # same thing
```

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

## Worked example — AL-01, end to end

**The claim:** *the agent can never process a refund by itself.*

Find the one place where the agent runs a tool. Every framework has one.

Before:

```python
def call_tool(name, args):
    return TOOLS[name](**args)
```

After:

```python
from llmsafety import alignment

# llmsafety: AL-01
refund = alignment.RefundBlocked()

def call_tool(name, args):
    try:
        refund.enforce(name)
    except alignment.ActionLocked:
        return escalate_to_human(name, args)      # the caller's decision
    return TOOLS[name](**args)
```

One import, one setup line, one call. Inside `enforce()`, two things happen —
the evidence line is appended, then it raises, so the tool never runs:

```python
def enforce(self, tool_name):                     # inside llmsafety
    if tool_name in self.denied or self.family.search(tool_name):
        evidence.fire("AL-01", tool=tool_name, action="denied")
        raise ActionLocked(f"AL-01: {tool_name} is locked pending human review")
    return True
```

llmsafety stops the action; the caller decides what the customer sees.

**Where the dispatch point lives.** The pattern is the same everywhere — find
where a tool name becomes an executed function, and guard it *before* the call.
A guard that runs afterwards is a log entry, not a control.

| Stack | The place |
|---|---|
| Claude Agent SDK | the `PreToolUse` hook |
| OpenAI function calling | the tool-call dispatch loop |
| LangChain / LangGraph | the tool-executor node, before `.invoke()` |
| MCP server | the top of the `call_tool` handler |
| Plain HTTP API | wherever an action string maps to a function |

**What it produces.** One evidence line per fire, written without any logging
code in the user's application:

```json
{"t":"2026-08-11T18:44:02+08:00","control":"AL-01","event":"denied","tool":"refund_order"}
```

and one audit row:

```
AL-01  bot can never refund by itself   ENFORCED   my_agent.py:6   fired 3×/30d  ✅
```

which is all three properties at once — *enforced* (the marker was found at
that line), *observed* (it fired three times in thirty days), *auditable* (the
row is dated, repeatable, and backed by the evidence file).

**Another domain.** `RefundBlocked()` is `ToolBlocked()` with the contact-centre
parameters already filled in. Same machine, different words:

```python
alignment.ToolBlocked(control="AL-01", denied=["wire_transfer", "close_account"])  # a bank
alignment.ToolBlocked(control="AL-01", denied=["prescribe", "discharge"])          # a hospital
alignment.ToolBlocked(control="AL-01", family=r"force.?push|drop.?table")          # a code agent
```

This is the generalisation the whole catalog rests on: the **pattern** is
universal, the **parameters** are the deployment's own.

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
- **Auditability** — `uv run llmsafety audit` (read-only, run by the user, on
  their machine) connects register + `# llmsafety: <ID>` markers + evidence log
  + proof tests into a dated report: terminal table for the developer,
  `--json` evidence artifact for the archive, `--html` one-file safety page
  for the auditor. Exit non-zero on a broken claim gates CI:

```yaml
- uses: astral-sh/setup-uv@v5
- run: uv sync --locked
- run: uv run llmsafety audit        # a broken claim turns the build red
```

  Shipping the CLI requires an entry point in `pyproject.toml`, which `0.1.0`
  does not yet declare:

```toml
[project.scripts]
llmsafety = "llmsafety.cli:main"
```

The helpers are optional. A user who keeps their own enforcement adds the
marker and one `evidence.fire("AL-01")` line, and all three properties still
hold — llmsafety never demands to be the enforcer, only to be able to prove
the enforcer exists, fires, and stays proven.

## Totals

**44 classes: 20 guard · 9 detector · 15 attest.**
