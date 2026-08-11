"""The safety control register — a register you keep in code, in git, reviewed in PRs.

Extracted from a production multi-tenant AI contact centre.

WHY IN the package AND NOT IN A DOCUMENT. A real audit found the claim "a
written guardrail inventory is kept in the repo and updated together with the
system it describes" to be FALSE — the inventory lived in a gitignored docs
folder. Putting the register in shipped source makes the claim true by
construction: it moves with the code, it cannot drift without a diff, and both
the safety page and the controls report can be generated from it.

Three evidence classes, deliberately distinguished (SOC 2 makes the same split
between test-of-design and test-of-operating-effectiveness):

    attestation — is the control configured on, right now?
    detective   — did it fire, and can you show the records?
    test        — how do you know it still works when it has not fired?

A control's live STATUS is deliberately not a field here. Compute it per
request from evidence — a hardcoded status is exactly the unverifiable claim a
register exists to replace.

See ``docs/documentations/control-register.md`` for the full pattern and
``docs/documentations/control-catalog.md`` for the reference catalog rendered as a document.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

STATUS = "experimental"

#: Category order, matching the five domains (underscore form, per Python naming).
CATEGORIES = ("alignment", "guardrails", "fairness", "review_routing", "compliance")

CATEGORY_LABELS = {
    "alignment": "Alignment",
    "guardrails": "Guardrails",
    "fairness": "Fairness",
    "review_routing": "Review routing",
    "compliance": "Compliance",
}

#: attestation — armed right now? / detective — did it fire? / test — still proven?
EVIDENCE_CLASSES = ("attestation", "detective", "test")

#: ``not-instrumented`` is first-class on purpose: an uninstrumented control
#: says so, rather than rendering a reassuring zero.
CAPTURE_MODES = ("event", "private-note", "derived", "config", "not-instrumented")

#: trained — vendor model training (broad harm only, you own none of it);
#: prompt — instructions (shape behaviour, do not enforce); screening — runtime
#: input/output checks you run; authorization — what the agent may DO;
#: platform — outside the request path (retention, backups, logs, SLAs).
CONTROL_LAYERS = ("trained", "prompt", "screening", "authorization", "platform")

#: mutation — control deliberately broken, suite went red, restored (strongest);
#: prod-read — live state read from production (snapshot, not a guard);
#: unproven — neither was possible, stated rather than left to look equal.
VERIFIED_BY = ("mutation", "prod-read", "unproven")

#: The OWASP Agentic Security Initiative threat list (ASI 2026 taxonomy),
#: ASI01–ASI10. Named in ONE place so a control's ``asi_name`` cannot drift from
#: the threat it claims to address, and so a threat with no controls still has a
#: name to be reported under.
ASI_THREATS = {
    "ASI01": "Agent Goal Hijack",
    "ASI02": "Tool Misuse and Exploitation",
    "ASI03": "Identity and Privilege Abuse",
    "ASI04": "Agentic Supply Chain Vulnerabilities",
    "ASI05": "Unexpected Code Execution",
    "ASI06": "Memory and Context Poisoning",
    "ASI07": "Insecure Inter-Agent Communication",
    "ASI08": "Cascading Agent Failures",
    "ASI09": "Human-Agent Trust Exploitation",
    "ASI10": "Rogue Agents",
}

#: Why a threat has no controls — "absent is never zero", one level up.
#:
#: The control-level rule (``capture="not-instrumented"`` requires a ``gap``)
#: makes an unmeasured control say so. It cannot help at the THREAT level: a
#: threat nothing maps to renders as a blank row, and a blank is unreadable — it
#: could mean the threat was missed, or that the architecture cannot exhibit it.
#: Those are opposite facts, and a coverage score that conflates them is
#: dishonest in the optimistic direction.
#:
#:   covered        — one or more controls map to it. DERIVED, never declared.
#:   gap            — it applies to this system and no control covers it yet.
#:   not-applicable — the architecture cannot exhibit it, with the reason why.
#:   undeclared     — no controls and no declared posture. The failure state.
#:
#: ``undeclared`` is representable on purpose rather than prevented: a register
#: that cannot express its own omission hides it. The tests assert the reference
#: catalog carries none.
THREAT_STATUSES = ("covered", "gap", "not-applicable", "undeclared")

#: The statuses a posture may DECLARE. "covered" is absent deliberately —
#: coverage is computed from the controls, never asserted, for the same reason a
#: control carries no hardcoded live status.
DECLARABLE_THREAT_STATUSES = ("gap", "not-applicable")


@dataclass(frozen=True)
class ThreatPosture:
    """A declared position on a threat that no control maps to.

    ``reason`` is required on both statuses: an unexplained "not applicable" is
    how a real obligation gets waved away, and an unexplained gap cannot be
    actioned. For ``not-applicable``, state the architectural fact that makes it
    true and the change that would revoke it.
    """

    #: ASI id, e.g. "ASI07". Must be a key of :data:`ASI_THREATS`.
    threat: str
    status: str
    reason: str


@dataclass(frozen=True)
class SafetyControl:
    """One row an auditor can walk: what you claim, how it is proven.

    A register has two audiences: ``claim`` is written for an auditor as a
    falsifiable statement; ``plain`` is the same control in the operator's
    words (~7 words, no jargon). ``gap`` is required whenever ``capture`` is
    ``"not-instrumented"`` — a declared blind spot, in the reference catalog
    and in yours. The deployment-owned fields (``source``, ``failing``,
    ``verified_by``, ``verified_how``) are left empty in the reference catalog
    — they describe YOUR system's state, not the control's design. Fill them
    in when you adopt a row.
    """

    id: str
    category: str
    plain: str
    claim: str
    evidence: str
    capture: str
    layer: str
    short_label: str | None = None
    owasp: str | None = None
    asi: str | None = None
    asi_name: str | None = None
    asi_why: str | None = None
    notes: str | None = None
    source: str | None = None
    gap: str | None = None
    failing: bool = False
    verified_by: str | None = None
    verified_how: str | None = None


#: The reference catalog: every control extracted from the originating
#: production system, scrubbed of deployment specifics. Ids keep their original
#: numbering — including the gaps. Numbering gaps are audit leads: in the
#: originating system, questioning them uncovered real, shipped guardrails that
#: had no register entry (and production evidence written against ids the page
#: did not define). Voice-channel controls (VC-*) are filed under guardrails.
REFERENCE_CONTROLS: tuple[SafetyControl, ...] = (
    SafetyControl(
        id="AL-01",
        category="alignment",
        short_label="refund tool blocked",
        plain="bot can never refund by itself",
        claim="The customer-service agent can never process a refund or return by itself.",
        evidence="detective",
        capture="event",
        layer="authorization",
        owasp="LLM02",
        asi="ASI02",
        asi_name="Tool Misuse and Exploitation",
        asi_why="a tool it may never use",
        notes="Enforced by a deny-by-default pre-tool-use hook over locked review actions. Mutation-verified two ways: gate forced to allow, and the matching pattern deleted — both turned the suite red.",
    ),
    SafetyControl(
        id="AL-02",
        category="alignment",
        short_label="built-in tools denied",
        plain="bot may only use approved tools",
        claim="The agent can only call approved MCP tools; the model's built-in tools (shell, file writes, web fetch) are always denied.",
        evidence="detective",
        capture="event",
        layer="authorization",
        owasp="LLM02",
        asi="ASI05",
        asi_name="Unexpected Code Execution",
        asi_why="shell and file access is the code-execution path",
        notes="Mutation-verified: non-MCP tools allowed, gate suite went red. Counter-intuitive and worth stating: the agent SDK's allowed-tools list is an AUTO-APPROVE list, not a restriction, so the built-ins stay reachable unless something denies them — the deny check is installed unconditionally for exactly that reason, and every prompt on this path carries untrusted customer text. Was emitted in production for every non-refund tool denial but MISSING from the register: evidence was written against a control id the page did not define, so those denials rendered nowhere. Found because the numbering gap was questioned.",
    ),
    SafetyControl(
        id="AL-03",
        category="alignment",
        short_label="empty run escalates",
        plain="a reply that sends nothing goes to a human",
        claim="A run that delivers nothing to the customer escalates to a human instead of failing silently.",
        evidence="detective",
        capture="private-note",
        layer="screening",
        owasp="LLM02",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="stops a silent failure propagating",
        notes="Mutation-verified: outcome reporter made to never report an empty run, suite went red.",
    ),
    SafetyControl(
        id="AL-04",
        category="alignment",
        short_label="provider error hidden",
        plain="hides AI error text from customers",
        claim="Provider failure text rendered as an assistant reply is swallowed, never sent to the customer, and the turn switches to the fallback provider.",
        evidence="detective",
        capture="event",
        layer="screening",
        owasp="LLM02",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="provider error text does not leak downstream",
        notes="Mutation-verified: recogniser stopped matching provider error text, test went red. Was a free id filled by a real but unregistered feature — found by continuing to check numbering gaps rather than trusting a string search. Deliberate asymmetry: if a tool has ALREADY executed, the turn is NOT retried, because re-running could place the same order or send the same message twice — a plain error is surfaced and the caller escalates instead. Declared gap: only counted from when recording began; earlier occurrences were never recorded.",
    ),
    SafetyControl(
        id="AL-05",
        category="alignment",
        short_label="refund promise detected",
        plain="catches the bot promising a refund",
        claim="A first-person refund promise in a bot reply is detected and recorded.",
        evidence="detective",
        capture="event",
        layer="screening",
        owasp="LLM02",
        asi="ASI09",
        asi_name="Human-Agent Trust Exploitation",
        asi_why="the bot claiming authority it does not have",
        notes="Mutation-verified via a detector-parity test. Deliberately reworded from a prevention claim: the canary is explicitly log-only and never blocks — the promise still reaches the customer and is recorded afterwards; prevention is the refund tool-gate's job, and claiming prevention here is exactly the unverifiable claim the register exists to remove. Capture migrated from derived (regex re-scan of every sent reply on each page load, a large share of page time) to an event stamped when a reply is flagged. Declared gaps: it detects, it does not stop; live counting began at deploy (a partial first day) across every reply path; earlier hits survive only in frozen daily snapshots.",
    ),
    SafetyControl(
        id="AL-06",
        category="alignment",
        short_label="tools deny-by-default",
        plain="agent gets zero tools unless granted",
        claim="A custom agent has NO tools unless each verb is explicitly granted in its capabilities file; a failed or missing grants read denies all rather than allowing any.",
        evidence="attestation",
        capture="config",
        layer="authorization",
        owasp="LLM02",
        asi="ASI03",
        asi_name="Identity and Privilege Abuse",
        asi_why="no grant means no privilege",
        notes="Mutation-verified: granting every tool turned the suite red. Fail direction is closed: a broken capabilities file yields zero tools. Declared gap: the check proves nothing is granted by accident, not that a granted list is sensible.",
    ),
    SafetyControl(
        id="AL-07",
        category="alignment",
        short_label="sealed workspace",
        plain="each chat runs in its own sealed box",
        claim="Each conversation runs in a sealed workspace: a per-session config directory, no inherited settings, and no ambient MCP servers.",
        evidence="attestation",
        capture="config",
        layer="authorization",
        owasp="LLM06",
        asi="ASI06",
        asi_name="Memory and Context Poisoning",
        asi_why="nothing leaks between conversations",
        notes="Prod-read: production's auth mode makes the per-session config directory unconditional. Declared gap: one exception exists on a developer's own laptop, never in production.",
    ),
    SafetyControl(
        id="AL-08",
        category="alignment",
        short_label="no retry after action",
        plain="never sends the same message twice",
        claim="Once a side-effect tool has run (message sent, order placed), the turn is never retried — a later provider failure surfaces as an error instead of risking the action twice.",
        evidence="attestation",
        capture="config",
        layer="screening",
        owasp="LLM02",
        asi="ASI02",
        asi_name="Tool Misuse and Exploitation",
        asi_why="prevents the same action running twice",
        notes="Mutation-verified: marking all tools safe to re-run turned the latch suite red. Declared gap: when the latch stops a retry, the customer-visible record says 'AI error' without naming the retry-block as the reason.",
    ),
    SafetyControl(
        id="AL-09",
        category="alignment",
        short_label="reply actually delivered",
        plain="keeps trying if a reply fails to send",
        claim="A reply the agent has produced is retried across a service restart rather than discarded, and a reply that never reaches the customer is recorded as an incident.",
        evidence="detective",
        capture="event",
        layer="platform",
        owasp="LLM09",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="a failed hand-off must not silently swallow the answer",
        notes="Registered after a real incident: the agent wrote an answer while a deploy was replacing the messaging service, the single delivery call failed, and the reply was discarded with only a warn line — nothing retried it, nothing recorded it, and the page showed a healthy account while a customer sat looking at silence. Two mutations, both caught: retry rule forced to never retry, and backoff shortened to inside a restart window. Declared gap: covers the DELIVERY step only — if the AI service itself restarts mid-run, the answer dies with the process and that turn leaves no record at all.",
    ),
    SafetyControl(
        id="GD-01",
        category="guardrails",
        short_label="sender rate limit",
        plain="one sender cannot flood the bot",
        claim="A single sender cannot flood the bot; excess messages are shed without losing real ones.",
        evidence="detective",
        capture="event",
        layer="screening",
        owasp="LLM10",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="one sender exhausting the agent's capacity",
        notes="Mutation-verified: rate check forced to allow, suite went red. Declared gap: on channels where the flood is blocked before the tenant is resolved, those blocks cannot be attributed and are not counted.",
    ),
    SafetyControl(
        id="GD-02",
        category="guardrails",
        short_label="injection detected",
        plain="spots customers trying to hijack the bot",
        claim="Prompt-injection attempts are detected and recorded.",
        evidence="detective",
        capture="event",
        layer="screening",
        owasp="LLM01",
        asi="ASI01",
        asi_name="Agent Goal Hijack",
        asi_why="the classic goal-hijack attempt",
        notes="Mutation-verified: detector made to never flag, suite went red. Capture migrated from derived (regex re-scan of all stored inbound text on every page load — most of the page's render time) to an event stamped at detection time, with the page counting rows. Declared blind spots: counting began at deploy (a partial first day), customer-service path only, messages merged by the inbound debounce are scanned once, console/test traffic is included, and detection patterns are English-only. The old any-channel scan survives only in frozen daily snapshots.",
    ),
    SafetyControl(
        id="GD-03",
        category="guardrails",
        short_label="no answer without evidence",
        plain="no proof, no answer — hands to a human",
        claim="An agent granted the strict-grounding capability never answers from nothing: a reply built on zero knowledge-base hits and no tool call is rewritten to a handover instead of being sent.",
        evidence="detective",
        capture="private-note",
        layer="screening",
        owasp="LLM09",
        asi="ASI09",
        asi_name="Human-Agent Trust Exploitation",
        asi_why="answering from nothing is false confidence",
        notes="Mutation-verified: guard made to always pass replies, suite went red. Was a real, shipped guardrail with no register entry — found by questioning a numbering gap rather than trusting a string search. Known evidence limit (not an implementation one): the guard rewrites the reply to the handover marker and downstream treats it exactly like a model-initiated handover — same flip, same note wording — so the note proves A handover happened but not that GROUNDING caused it, and the number of ungrounded answers prevented is not separately countable; the guard's own log lines are not queryable evidence. Applies only to agents granted the strict setting, not all.",
    ),
    SafetyControl(
        id="GD-04",
        category="guardrails",
        short_label="inbound text cap",
        plain="cuts very long customer messages",
        claim="Customer text is capped at a fixed character limit before it reaches the model, the trace, or billing.",
        evidence="attestation",
        capture="config",
        layer="screening",
        owasp="LLM10",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="an oversized payload crowding the context window",
        notes="Mutation-verified. The cap is compile-time with no env override, and deliberately sits above every channel's native message-length limit, so no channel-legal message is ever truncated — it only bites stitched or pasted payloads. Admin/console input is trusted and uncapped by design, which is why this is not a fleet-wide claim about all input. Declared gap: truncation is not recorded, so frequency is unknown.",
    ),
    SafetyControl(
        id="GD-05",
        category="guardrails",
        short_label="loop breaker",
        plain="stops the bot replying to itself",
        claim="Runaway bot loops are broken after a fixed short run of consecutive bot replies with no customer message in between.",
        evidence="detective",
        capture="private-note",
        layer="screening",
        owasp="LLM10",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="a runaway loop consuming budget and trust",
        notes="Mutation-verified: verdict forced to ok, guard suite went red. Keys on consecutive bot replies with no inbound between — a human message always breaks the chain.",
    ),
    SafetyControl(
        id="GD-06",
        category="guardrails",
        short_label="turn cap",
        plain="one question cannot run forever",
        claim="A single customer question is capped at a fixed number of model turns, so one run cannot loop forever.",
        evidence="attestation",
        capture="config",
        layer="screening",
        owasp="LLM10",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="one question looping without end",
        notes="Prod-read: the env override is unset in production, so the code default applies. Taxonomy note: filed under guardrails rather than alignment on purpose — this is runaway-loop / unbounded-consumption resistance, the same family as the loop breaker; filling a numbering gap in another category would have been the wrong taxonomy. Declared gaps: the limit is server-tunable so the real number may differ, and hitting it is not recorded.",
    ),
    SafetyControl(
        id="GD-07",
        category="guardrails",
        short_label="hourly reply cap",
        plain="caps bot replies per chat per hour",
        claim="The bot cannot exceed a fixed hourly per-conversation reply cap; past it the AI is muted and staff are asked to take over.",
        evidence="detective",
        capture="private-note",
        layer="screening",
        owasp="LLM10",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="one conversation burning budget without end",
        notes="Mutation-verified. Registered late: a guardrail the operator had tuned personally but which was never on the page — they remembered the number and could not find it. The threshold's history is kept deliberately: at a lower value it once muted the bot mid-sale on a talkative but genuine customer, so it was raised — lowering it back is the known regression to avoid. The loop breaker is the real runaway detector; this is a cost/abuse backstop. Declared gaps: counted together with the loop breaker (both leave the same kind of note, so the page cannot tell them apart), the value is server-tunable, and zero turns it off.",
    ),
    SafetyControl(
        id="GD-08",
        category="guardrails",
        short_label="echo direction guard",
        plain="phone reply copy can never wake the bot",
        claim="A coexistence echo (a message the business sent from its own messaging app on the same number) is stored as the business's outgoing reply — it can never be mistaken for a customer message, trigger an AI reply, or flip a human-owned conversation back to the AI; an echo whose sender is not the inbox's own number is dropped and recorded.",
        evidence="detective",
        capture="event",
        layer="screening",
        owasp="LLM06",
        asi="ASI09",
        asi_name="Human-Agent Trust Exploitation",
        asi_why="the bot answering the business's own staff",
        notes="Mutation-verified: direction assertion forced false stored both forged and self-consistent forged echoes, tests went red. The echo sender must equal the inbox's STORED own number (with a display-number metadata fallback; an empty value never matches); a mismatch is dropped and stamps a direction-mismatch guardrail event.",
    ),
    SafetyControl(
        id="GD-09",
        category="guardrails",
        short_label="staff reply guard",
        plain="the bot never answers your own staff",
        claim="On the line that delivers staff their alert messages, a reply from a recognised staff member is withheld from the bot while everyone else on that line is served as a customer; a recognition lookup that fails is recorded as its own state rather than counted as a screening, so a blind guard cannot read as a quiet one.",
        evidence="detective",
        capture="event",
        layer="screening",
        owasp="LLM06",
        asi="ASI09",
        asi_name="Human-Agent Trust Exploitation",
        asi_why="the bot answering the business's own staff",
        notes="Replaces a blanket 'ignore every message on the alert line' rule that held only while the line had no customers — a real inbox once lost weeks of inbound messages at info log level, looking exactly like silence. Mutation-verified with a designed split: the mutation removed the guard, not the line, so customer-path tests still passed while every staff-protection test failed. Event kinds distinguish caught / could-not-decide / recognition-set-changed, plus a checked counter incremented only on successful reads. Declared gaps: recognition depends on staff numbers being configured; the drop is guaranteed while evidence writes are best-effort; and when the alert channel is off entirely the guard does not run — the checked counter then reads absent rather than zero, the honest signal.",
    ),
    SafetyControl(
        id="VC-01",
        category="guardrails",
        short_label="voice reply guard",
        plain="checks every spoken reply before the caller hears it",
        claim="No model output is spoken verbatim on a voice call: an exact no-reply sentinel is silenced, and a handover prefix is stripped, its visible line spoken, and the bot muted for the remainder of that call.",
        evidence="test",
        capture="event",
        layer="screening",
        owasp="LLM05",
        asi="ASI05",
        asi_name="Unexpected Code Execution",
        asi_why="unvetted model output straight into a caller's ear",
        notes="Voice controls were registered at build time, per the standing rule that a control which cannot be evidenced is not finished — the gateway declares its missing instrumentation rather than hiding behind a reassuring zero. Mutation-verified at the unit level. Declared gaps: a reply-grounding golden set exists but its runner is not yet wired, so 'test' evidence currently means the unit suite, not the golden set; event emission is fail-open — a database fault under-counts fires without touching the call.",
    ),
    SafetyControl(
        id="VC-02",
        category="guardrails",
        short_label="voice canary",
        plain="flags risky spoken replies, never blocks them",
        claim="Every reply actually spoken on a voice call is screened log-only for protocol residue, unsafe promises and language mismatch; the canary never blocks or mutates a reply.",
        evidence="detective",
        capture="event",
        layer="screening",
        owasp="LLM05",
        asi="ASI05",
        asi_name="Unexpected Code Execution",
        asi_why="the log-only screen that notices what the guard cannot",
        notes="Mutation-verified: residue check removed, unit test went red. Declared gaps: detector consolidation with the text-channel canary remains open — two canaries, two vocabularies, until one shared source exists; emission is fail-open and per-fire.",
    ),
    SafetyControl(
        id="VC-03",
        category="guardrails",
        short_label="voice wallet gate",
        plain="no money, the number does not answer",
        claim="A zero-balance account's voice line refuses pickup before the greeting, and the check fails OPEN on errors so a billing outage never silences a healthy tenant's calls.",
        evidence="test",
        capture="event",
        layer="authorization",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="unmetered calls burning tenant balance",
        notes="Unproven: exercised live against a local stack (a short call moved the wallet balance; the refusal path was manually forced) but no automated test yet — declared rather than hidden. Refusals emit their own event kind, and the charge side is evidenced by wallet-ledger rows tagged with a voice source.",
    ),
    SafetyControl(
        id="VC-04",
        category="guardrails",
        short_label="voice handover flip",
        plain="handover moves the call to your staff",
        claim="A voice handover deterministically mutes the bot for that call and flips the messaging-side conversation to a human handler via the takeover route — relay-enforced, never a tool call.",
        evidence="detective",
        capture="event",
        layer="screening",
        asi="ASI06",
        asi_name="Memory and Context Poisoning",
        asi_why="escalation the model asks for but must not control",
        notes="No verification mode recorded yet. Declared gaps: the warm phone transfer does not exist until the telephony phase, and an unset handover-target setting skips the handler flip with only a log line — the event still fires, so the miss is at least counted.",
    ),
    SafetyControl(
        id="FA-01",
        category="fairness",
        short_label="same kit for everyone",
        plain="every customer gets the same instructions",
        claim="Every customer of an agent gets the same instructions: the same kit files and the same escalation ladder.",
        evidence="attestation",
        capture="config",
        layer="prompt",
        notes="Prod-read: a live attestation confirms every active agent has all required kit files. The remaining gap is narrower than not-instrumented: PRESENCE of the required kit files is checked; the escalation ladder inside them is not compared.",
    ),
    SafetyControl(
        id="FA-02",
        category="fairness",
        short_label="no VIP lane",
        plain="no VIP lane — everyone gets the same bot",
        claim="A customer's tier, name or country never reaches the reply path — a VIP and a first-time customer get the identical bot.",
        evidence="test",
        capture="config",
        layer="screening",
        notes="Mutation-verified: injecting a tier reference into the retrieval path made the scan fail. Proven by ABSENCE — a test fails the build if tier/VIP/priority ever appears on the reply path. Declared boundary: marketing campaigns DO segment by tier; that is outreach, not service.",
    ),
    SafetyControl(
        id="FA-03",
        category="fairness",
        short_label="same service any language",
        plain="same service in any language",
        claim="The language is detected per message, so service does not depend on which language the customer writes in.",
        evidence="attestation",
        capture="config",
        layer="screening",
        notes="Mutation-verified: language detection forced to null turned the interceptor suite red. Declared nuance: per-message detection follows a customer switching language mid-chat; answer quality still depends on the knowledge-base content available in that language.",
    ),
    SafetyControl(
        id="FA-04",
        category="fairness",
        short_label="language limits are visible",
        plain="language limits are a visible setting",
        claim="A business may restrict which languages it supports, but only through visible settings — never hidden inside the agent's personality.",
        evidence="attestation",
        capture="config",
        layer="prompt",
        notes="Prod-read: the languages settings column is present in production, editable and readable. Declared gap: nothing stops a tenant ALSO writing a language rule into their agent files, where it would not show here.",
    ),
    SafetyControl(
        id="FA-05",
        category="fairness",
        short_label="blocking is deliberate only",
        plain="only staff can block a customer",
        claim="The only per-customer difference in service is an explicit staff 'blocked' flag — never a trait the system inferred.",
        evidence="detective",
        capture="not-instrumented",
        layer="screening",
        gap="Blocking is a deliberate staff action but is not recorded as a safety event, so who was blocked, and when, does not appear on the evidence surface.",
        notes="Prod-read: the blocked column is present in production; blocked contacts are skipped by the inbound path. Declared gap: blocking is a deliberate staff action but is not recorded as a safety event, so who was blocked, and when, does not appear on the page.",
    ),
    SafetyControl(
        id="RR-01",
        category="review_routing",
        short_label="handover in code",
        plain="code hands the chat over, not the bot",
        claim="An escalation flips the conversation to a human in CODE, not by asking the model to call a tool.",
        evidence="detective",
        capture="private-note",
        layer="screening",
        owasp="LLM09",
        asi="ASI09",
        asi_name="Human-Agent Trust Exploitation",
        asi_why="the model must not merely claim it escalated",
        notes="Mutation-verified: handover marker made unrecognisable, guard suite went red. Incident drill-through links to an operator-safe conversation viewer that takes the tenant from the URL and filters on both ids; the tenant-facing route is deliberately not reused because it resolves the tenant from the viewer's session and would open the wrong tenant from a cross-tenant page.",
    ),
    SafetyControl(
        id="RR-02",
        category="review_routing",
        short_label="re-check before sending",
        plain="drops the bot reply if staff replied first",
        claim="Conversation ownership is re-checked immediately before sending: if a human took over while the AI was composing, the AI's reply is thrown away.",
        evidence="detective",
        capture="not-instrumented",
        layer="screening",
        owasp="LLM09",
        asi="ASI09",
        asi_name="Human-Agent Trust Exploitation",
        asi_why="the bot talking over a human who already replied",
        gap="The discarded reply is logged but not recorded as a safety event, so how often a human was protected from being talked over is unknown.",
        notes="Unproven: the re-check is inline in the webhook with no exported function, so a unit test cannot reach it without refactoring. Declared gap: the discarded reply is logged but not recorded as a safety event, so how often a human was protected from being talked over is unknown.",
    ),
    SafetyControl(
        id="RR-03",
        category="review_routing",
        short_label="one open handover per chat",
        plain="only one open handover per chat",
        claim="The database itself allows only one open human-handling session per conversation, so response-time reporting cannot double-count.",
        evidence="attestation",
        capture="config",
        layer="platform",
        notes="Prod-read: the unique partial index is present in production. Declared limit: it guarantees at most one OPEN session per conversation, not that the session was closed at the right moment.",
    ),
    SafetyControl(
        id="RR-04",
        category="review_routing",
        short_label="failed mute surfaced",
        plain="shouts if the bot fails to go quiet",
        claim="When muting the AI after a handover fails, the failure is surfaced loudly rather than leaving a live bot on a handed-over conversation.",
        evidence="detective",
        capture="private-note",
        layer="screening",
        owasp="LLM09",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="a failed handover must not propagate silently",
        notes="Mutation-verified: severity downgraded from critical, test went red. The private note is the durable record; a real-time operator ping is layered on top. Design rule: the record is written whether or not the alert was delivered, so a missing alert never means a missing incident — alert DELIVERY itself is log-only, not evidence.",
    ),
    SafetyControl(
        id="RR-05",
        category="review_routing",
        short_label="one alert per conversation",
        plain="one alert per chat, not per message",
        claim="Staff get one alert per conversation, not one per message — and an escalation always alerts regardless.",
        evidence="attestation",
        capture="config",
        layer="platform",
        asi="ASI08",
        asi_name="Cascading Agent Failures",
        asi_why="an alert storm trains staff to ignore alerts",
        notes="Mutation-verified: dedup forced to always allow, tests went red. Declared gap: the dedup lives in memory, so a restart can allow one repeat alert. Escalations bypass the dedup deliberately — they are never suppressed.",
    ),
    SafetyControl(
        id="RR-07",
        category="review_routing",
        short_label="handover SLA",
        plain="alerts if a waiting customer is left too long",
        claim="After a human takes a conversation over, a customer left waiting past the SLA raises a staff alert, and the breach is recorded even when no alert could be delivered.",
        evidence="detective",
        capture="event",
        layer="platform",
        owasp="LLM09",
        notes="Mutation-verified. Measurement basis matters: the wait is measured from the HANDOVER, not the customer's last message — measuring from the message once recorded an absurd multi-day 'breach' seconds after someone took over a stale conversation; nobody can answer a message before they own it. Rows carrying the old basis predate the handover timestamp and may include time before anyone was responsible. Declared gaps: only handovers after the feature shipped can be measured fairly, and the alert has nowhere to go until a staff notification channel is configured.",
    ),
    SafetyControl(
        id="RR-09",
        category="review_routing",
        short_label="handover auto-reset",
        plain="idle chats go back to the bot",
        claim="A conversation handed to humans and then left idle returns to the AI automatically after a fixed idle window rather than stalling forever.",
        evidence="attestation",
        capture="config",
        layer="platform",
        notes="Unproven: no test covers the idle-reset constant.",
    ),
    SafetyControl(
        id="CP-01",
        category="compliance",
        short_label="session memory retention",
        plain="old chat memory is deleted on schedule",
        claim="Conversation session memory is deleted on a fixed retention schedule.",
        evidence="attestation",
        capture="not-instrumented",
        layer="platform",
        owasp="LLM06",
        asi="ASI06",
        asi_name="Memory and Context Poisoning",
        asi_why="stale memory re-teaching old mistakes",
        gap="The retention value lives in another service's environment, which the attesting service cannot read to prove it.",
        notes="Prod-read: the retention window is set in the production environment. Declared gap: the retention value lives in the other service's environment, which the attesting service cannot read to prove it.",
    ),
    SafetyControl(
        id="CP-02",
        category="compliance",
        short_label="backups encrypted",
        plain="backups are encrypted",
        claim="Database backups are encrypted at rest.",
        evidence="attestation",
        capture="not-instrumented",
        layer="platform",
        owasp="LLM06",
        gap="Encryption only happens when a passphrase is configured; without one, backups are plain compressed dumps.",
        notes="The declared-failure pattern applies here: an unencrypted-backups state is worth flagging with the failing flag rather than describing in prose, because a renderer cannot see prose — and a compliance page that groups a broken control with healthy ones reads as an all-clear.",
    ),
    SafetyControl(
        id="CP-03",
        category="compliance",
        short_label="phone masked in logs",
        plain="logs show only the last few digits",
        claim="A customer's phone number appears in logs only as a masked suffix (last few digits).",
        evidence="attestation",
        capture="config",
        layer="platform",
        owasp="LLM06",
        notes="Mutation-verified: mask made to return the full number, suite went red. Registered together with the fix itself, per the standing rule — the claim had been made for months while multiple log sites wrote full numbers. Masking is unconditional, with no env flag. Declared gaps: proven by tests, not a live check; covers logs only — traces in the tracing platform keep the full number by deliberate operator decision.",
    ),
    SafetyControl(
        id="CP-05",
        category="compliance",
        short_label="admin 2FA",
        plain="admin logins need a second factor",
        claim="Platform super-admin accounts require a second factor.",
        evidence="attestation",
        capture="config",
        layer="authorization",
        owasp="LLM06",
        notes="A dated point-in-time snapshot sitting beside a LIVE attestation on the same screen can disagree with it; the live reading is authoritative and the snapshot is marked historical, because an evidence page that contradicts itself teaches the reader to trust neither number. Also the register-first rule applied backwards: an attestation existed for a control the register did not define, which put an unexplained row on the coverage page.",
    ),
    SafetyControl(
        id="CP-06",
        category="compliance",
        short_label="one session per login",
        plain="a new device signs you out everywhere else",
        claim="Logging in on a new device signs the account out everywhere else.",
        evidence="attestation",
        capture="config",
        layer="authorization",
        owasp="LLM06",
        asi="ASI03",
        asi_name="Identity and Privilege Abuse",
        asi_why="a stolen old session must stop working",
        notes="Prod-read: login rotates the stored access token, which the JWT session id is checked against. Declared gaps: applies to tenant staff logins; session takeovers are not recorded, so the page cannot show how often it happened.",
    ),
    SafetyControl(
        id="CP-07",
        category="compliance",
        short_label="staff notes stay internal",
        plain="private notes never reach customers or the bot",
        claim="Staff-only private notes are never shown to a customer and never fed to the AI.",
        evidence="attestation",
        capture="config",
        layer="screening",
        owasp="LLM06",
        asi="ASI06",
        asi_name="Memory and Context Poisoning",
        asi_why="internal notes must not become AI context or customer text",
        notes="Unproven: no test covers private notes being withheld from the agent. Declared gap: covers the customer-service path; a note remains visible to any staff member with access to the conversation.",
    ),
    SafetyControl(
        id="CP-08",
        category="compliance",
        short_label="backups checked and pruned",
        plain="backups are tested, old ones deleted",
        claim="Every backup is verified readable before it is kept, and copies older than the retention window are deleted.",
        evidence="attestation",
        capture="config",
        layer="platform",
        owasp="LLM06",
        notes="Prod-read: backup files are present and pruned by retention. Declared gaps: the integrity check proves the file is readable, not that a full restore works; encryption is a separate control, and that one is currently off.",
    ),
    SafetyControl(
        id="CP-09",
        category="compliance",
        short_label="admin-only screens",
        plain="billing and settings are admin-only",
        claim="Billing, reports and connection settings are admin-only; ordinary staff are refused.",
        evidence="attestation",
        capture="config",
        layer="authorization",
        owasp="LLM06",
        asi="ASI03",
        asi_name="Identity and Privilege Abuse",
        asi_why="ordinary staff must not reach billing or settings",
        notes="Mutation-verified: role gate forced to pass everyone, suite went red. Declared gap: refusals are not recorded, so attempted access does not appear on the page.",
    ),
    SafetyControl(
        id="CP-10",
        category="compliance",
        short_label="scheduled jobs run",
        plain="a job that stops running shows up",
        claim="Every scheduled job records each run, and a job that stops firing becomes visible without anyone looking.",
        evidence="detective",
        capture="derived",
        layer="platform",
        owasp="LLM06",
        notes="Mutation-verified against a real scheduler-library gotcha (its previous-run call is always undefined off a scheduled instance — the mutation made every cron silently un-overdue-able). Evidence is DERIVED from the job-run table, not the guardrail event stream, deliberately: the event table is tenant-scoped with a non-null tenant FK and these are platform jobs with no tenant to attribute to, so the insert would throw exactly when an alert matters. Declared gaps: the operator-alert throttle is at-most-once-per-interval and in-memory, so it does not survive a restart; and the monitor runs INSIDE the service it monitors — if that service is down, nothing here reports. An external dead man's switch is the named fix and is not in place.",
    ),
    SafetyControl(
        id="CP-11",
        category="compliance",
        short_label="critical events page someone",
        plain="serious problems reach a real person",
        claim="A critical guardrail event reaches an operator who can act on it.",
        evidence="attestation",
        capture="config",
        layer="platform",
        owasp="LLM06",
        notes="The last hop is the one that fails: events can be emitted and routed correctly, then delivered to an operator channel that is not configured — and that failure affects every producer of critical severity at once. Route platform-internal alerts to an operator-owned channel, never to a tenant account that happens to have a working channel: that would leak operational detail and page people who cannot act. A gap may be declared, but never left undeclared.",
    ),
)

#: The originating system's declared position on every ASI threat its controls
#: do not reach. Three of ten, and they are not the same kind of absence — which
#: is the entire point of separating ``gap`` from ``not-applicable``.
#:
#: A catalog extracted from one production system SHOULD have holes; a catalog
#: that scores 10/10 was probably written against the threat list rather than
#: against a system. The holes are the finding, so they are declared here rather
#: than left to read as an oversight.
REFERENCE_THREAT_POSTURE: tuple[ThreatPosture, ...] = (
    ThreatPosture(
        threat="ASI04",
        status="gap",
        reason=(
            "Applies and is not covered. The system depends on a model vendor, third-party "
            "libraries and MCP tool servers, and no control in this catalog addresses the "
            "provenance or integrity of any of them. A real hole, declared rather than left blank."
        ),
    ),
    ThreatPosture(
        threat="ASI07",
        status="not-applicable",
        reason=(
            "Single-agent architecture: one agent serves a conversation and never messages "
            "another agent, so there is no inter-agent channel to secure. Revoke this the moment "
            "a second agent is introduced — the posture describes the architecture, not the intent."
        ),
    ),
    ThreatPosture(
        threat="ASI10",
        status="not-applicable",
        reason=(
            "Single-agent architecture: there is no fleet for a member to go rogue within and no "
            "agent registry to be impersonated in. Revoke this the moment agents are spawned "
            "dynamically or per-tenant."
        ),
    ),
)


def controls_for(
    category: str,
    controls: Sequence[SafetyControl] = REFERENCE_CONTROLS,
) -> list[SafetyControl]:
    """Return the controls filed under ``category``."""
    return [c for c in controls if c.category == category]


def find_control(
    control_id: str,
    controls: Sequence[SafetyControl] = REFERENCE_CONTROLS,
) -> SafetyControl | None:
    """Return the control with id ``control_id``, or ``None``."""
    for c in controls:
        if c.id == control_id:
            return c
    return None


@dataclass(frozen=True)
class RegisterCoverage:
    """Coverage profile of a register — what kind of evidence backs it, and
    where the declared holes are."""

    total: int
    by_evidence: dict[str, int]
    by_capture: dict[str, int]
    by_layer: dict[str, int]
    #: Ids whose capture is "not-instrumented" — declared blind spots, never hidden zeros.
    not_instrumented: list[str]
    #: Ids flagged ``failing=True`` — known broken, declared rather than described.
    failing: list[str]


def coverage(controls: Sequence[SafetyControl] = REFERENCE_CONTROLS) -> RegisterCoverage:
    """Aggregate a register into its coverage profile."""
    by_evidence = {k: 0 for k in EVIDENCE_CLASSES}
    by_capture = {k: 0 for k in CAPTURE_MODES}
    by_layer = {k: 0 for k in CONTROL_LAYERS}
    not_instrumented: list[str] = []
    failing: list[str] = []
    for c in controls:
        by_evidence[c.evidence] += 1
        by_capture[c.capture] += 1
        by_layer[c.layer] += 1
        if c.capture == "not-instrumented":
            not_instrumented.append(c.id)
        if c.failing:
            failing.append(c.id)
    return RegisterCoverage(
        total=len(controls),
        by_evidence=by_evidence,
        by_capture=by_capture,
        by_layer=by_layer,
        not_instrumented=not_instrumented,
        failing=failing,
    )


@dataclass(frozen=True)
class ThreatCoverageRow:
    """One ASI threat, and what this register has to say about it."""

    threat: str
    name: str
    status: str
    #: Ids of the controls mapped to this threat. Empty unless status is "covered".
    controls: list[str]
    #: The declared reason. Present for "gap" and "not-applicable", ``None`` otherwise.
    reason: str | None = None


@dataclass(frozen=True)
class ThreatCoverage:
    """Threat-side coverage: the answer to "how many of the ten do you cover?",
    with the two kinds of absence held apart."""

    #: Always the size of :data:`ASI_THREATS` — the denominator is the whole
    #: list, not the part you mapped.
    total: int
    covered: list[str]
    gaps: list[str]
    not_applicable: list[str]
    #: Threats with neither controls nor a declared posture. MUST be empty.
    undeclared: list[str]
    rows: list[ThreatCoverageRow]


def threat_coverage(
    controls: Sequence[SafetyControl] = REFERENCE_CONTROLS,
    posture: Sequence[ThreatPosture] = REFERENCE_THREAT_POSTURE,
) -> ThreatCoverage:
    """Aggregate controls and declared postures into a per-threat view.

    A posture is ignored for any threat that controls already reach: coverage is
    derived, so a stale "not-applicable" left behind after a control was added
    cannot suppress it. The contradiction is not silently resolved — the tests
    assert no posture is declared for a covered threat.
    """
    declared = {p.threat: p for p in posture}
    rows: list[ThreatCoverageRow] = []
    for threat, name in ASI_THREATS.items():
        mapped = [c.id for c in controls if c.asi == threat]
        if mapped:
            rows.append(ThreatCoverageRow(threat=threat, name=name, status="covered", controls=mapped))
            continue
        p = declared.get(threat)
        if p is None:
            rows.append(ThreatCoverageRow(threat=threat, name=name, status="undeclared", controls=[]))
        else:
            rows.append(
                ThreatCoverageRow(threat=threat, name=name, status=p.status, controls=[], reason=p.reason)
            )
    ids = lambda status: [r.threat for r in rows if r.status == status]  # noqa: E731
    return ThreatCoverage(
        total=len(rows),
        covered=ids("covered"),
        gaps=ids("gap"),
        not_applicable=ids("not-applicable"),
        undeclared=ids("undeclared"),
        rows=rows,
    )


__all__ = [
    "STATUS",
    "CATEGORIES",
    "CATEGORY_LABELS",
    "EVIDENCE_CLASSES",
    "CAPTURE_MODES",
    "CONTROL_LAYERS",
    "VERIFIED_BY",
    "ASI_THREATS",
    "THREAT_STATUSES",
    "DECLARABLE_THREAT_STATUSES",
    "ThreatPosture",
    "SafetyControl",
    "REFERENCE_CONTROLS",
    "REFERENCE_THREAT_POSTURE",
    "RegisterCoverage",
    "ThreatCoverageRow",
    "ThreatCoverage",
    "controls_for",
    "find_control",
    "coverage",
    "threat_coverage",
]
