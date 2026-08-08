# Control catalog

The reference catalog behind `aisafety/register` (TS) and
`aisafety.register` (Python) — **44 controls** extracted from a production
multi-tenant AI contact centre and scrubbed of deployment specifics. The code
module is the source of truth; this document is generated from the same data.

Ids keep their original numbering, **including the gaps** (RR-06, RR-08, CP-04
are absent). Numbering gaps are audit leads: in the originating system,
questioning them uncovered real, shipped guardrails that had no register entry.
Voice-channel controls (VC-*) are filed under guardrails.

Column key — **Evidence**: attestation (armed?) / detective (fired?) / test
(still proven?). **Capture**: how evidence is obtained; `not-instrumented`
is a declared blind spot, never a hidden zero. **Layer**: which layer enforces
it (prompt / screening / authorization / platform). **ASI**: OWASP Agentic
Security Initiative threat id; **OWASP**: LLM Top 10 id.

## Threat coverage (OWASP ASI)

| ASI threat | Controls mapped |
|---|---|
| ASI01 — Agent Goal Hijack | 1 |
| ASI02 — Tool Misuse | 2 |
| ASI03 — Privilege Abuse | 3 |
| ASI05 — Unexpected Code Execution / Unsafe Output | 3 |
| ASI06 — Memory & Context Poisoning | 4 |
| ASI08 — Cascading Failure / Resource Overload | 11 |
| ASI09 — Human Trust Exploitation | 6 |
| *(no agent-specific threat — fairness/compliance hygiene)* | 14 |

## Alignment (9)

| ID | Control | In the operator's words | Evidence | Capture | Layer | ASI | OWASP |
|---|---|---|---|---|---|---|---|
| AL-01 | refund tool blocked | bot can never refund by itself | detective | event | authorization | ASI02 | LLM02 |
| AL-02 | built-in tools denied | bot may only use approved tools | detective | event | authorization | ASI05 | LLM02 |
| AL-03 | empty run escalates | a reply that sends nothing goes to a human | detective | private-note | screening | ASI08 | LLM02 |
| AL-04 | provider error hidden | hides AI error text from customers | detective | event | screening | ASI08 | LLM02 |
| AL-05 | refund promise detected | catches the bot promising a refund | detective | event | screening | ASI09 | LLM02 |
| AL-06 | tools deny-by-default | agent gets zero tools unless granted | attestation | config | authorization | ASI03 | LLM02 |
| AL-07 | sealed workspace | each chat runs in its own sealed box | attestation | config | authorization | ASI06 | LLM06 |
| AL-08 | no retry after action | never sends the same message twice | attestation | config | screening | ASI02 | LLM02 |
| AL-09 | reply actually delivered | keeps trying if a reply fails to send | detective | event | platform | ASI08 | LLM09 |

### AL-01 — refund tool blocked

**Claim.** The customer-service agent can never process a refund or return by itself.

**Threat.** ASI02 (Tool Misuse) — a tool it may never use

Enforced by a deny-by-default pre-tool-use hook over locked review actions. Mutation-verified two ways: gate forced to allow, and the matching pattern deleted — both turned the suite red.

### AL-02 — built-in tools denied

**Claim.** The agent can only call approved MCP tools; the model's built-in tools (shell, file writes, web fetch) are always denied.

**Threat.** ASI05 (Unexpected Code Execution / Unsafe Output) — shell and file access is the code-execution path

Mutation-verified: non-MCP tools allowed, gate suite went red. Counter-intuitive and worth stating: the agent SDK's allowed-tools list is an AUTO-APPROVE list, not a restriction, so the built-ins stay reachable unless something denies them — the deny check is installed unconditionally for exactly that reason, and every prompt on this path carries untrusted customer text. Was emitted in production for every non-refund tool denial but MISSING from the register: evidence was written against a control id the page did not define, so those denials rendered nowhere. Found because the numbering gap was questioned.

### AL-03 — empty run escalates

**Claim.** A run that delivers nothing to the customer escalates to a human instead of failing silently.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — stops a silent failure propagating

Mutation-verified: outcome reporter made to never report an empty run, suite went red.

### AL-04 — provider error hidden

**Claim.** Provider failure text rendered as an assistant reply is swallowed, never sent to the customer, and the turn switches to the fallback provider.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — provider error text does not leak downstream

Mutation-verified: recogniser stopped matching provider error text, test went red. Was a free id filled by a real but unregistered feature — found by continuing to check numbering gaps rather than trusting a string search. Deliberate asymmetry: if a tool has ALREADY executed, the turn is NOT retried, because re-running could place the same order or send the same message twice — a plain error is surfaced and the caller escalates instead. Declared gap: only counted from when recording began; earlier occurrences were never recorded.

### AL-05 — refund promise detected

**Claim.** A first-person refund promise in a bot reply is detected and recorded.

**Threat.** ASI09 (Human Trust Exploitation) — the bot claiming authority it does not have

Mutation-verified via a detector-parity test. Deliberately reworded from a prevention claim: the canary is explicitly log-only and never blocks — the promise still reaches the customer and is recorded afterwards; prevention is the refund tool-gate's job, and claiming prevention here is exactly the unverifiable claim the register exists to remove. Capture migrated from derived (regex re-scan of every sent reply on each page load, a large share of page time) to an event stamped when a reply is flagged. Declared gaps: it detects, it does not stop; live counting began at deploy (a partial first day) across every reply path; earlier hits survive only in frozen daily snapshots.

### AL-06 — tools deny-by-default

**Claim.** A custom agent has NO tools unless each verb is explicitly granted in its capabilities file; a failed or missing grants read denies all rather than allowing any.

**Threat.** ASI03 (Privilege Abuse) — no grant means no privilege

Mutation-verified: granting every tool turned the suite red. Fail direction is closed: a broken capabilities file yields zero tools. Declared gap: the check proves nothing is granted by accident, not that a granted list is sensible.

### AL-07 — sealed workspace

**Claim.** Each conversation runs in a sealed workspace: a per-session config directory, no inherited settings, and no ambient MCP servers.

**Threat.** ASI06 (Memory & Context Poisoning) — nothing leaks between conversations

Prod-read: production's auth mode makes the per-session config directory unconditional. Declared gap: one exception exists on a developer's own laptop, never in production.

### AL-08 — no retry after action

**Claim.** Once a side-effect tool has run (message sent, order placed), the turn is never retried — a later provider failure surfaces as an error instead of risking the action twice.

**Threat.** ASI02 (Tool Misuse) — prevents the same action running twice

Mutation-verified: marking all tools safe to re-run turned the latch suite red. Declared gap: when the latch stops a retry, the customer-visible record says 'AI error' without naming the retry-block as the reason.

### AL-09 — reply actually delivered

**Claim.** A reply the agent has produced is retried across a service restart rather than discarded, and a reply that never reaches the customer is recorded as an incident.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — a failed hand-off must not silently swallow the answer

Registered after a real incident: the agent wrote an answer while a deploy was replacing the messaging service, the single delivery call failed, and the reply was discarded with only a warn line — nothing retried it, nothing recorded it, and the page showed a healthy account while a customer sat looking at silence. Two mutations, both caught: retry rule forced to never retry, and backoff shortened to inside a restart window. Declared gap: covers the DELIVERY step only — if the AI service itself restarts mid-run, the answer dies with the process and that turn leaves no record at all.

## Guardrails (13)

| ID | Control | In the operator's words | Evidence | Capture | Layer | ASI | OWASP |
|---|---|---|---|---|---|---|---|
| GD-01 | sender rate limit | one sender cannot flood the bot | detective | event | screening | ASI08 | LLM10 |
| GD-02 | injection detected | spots customers trying to hijack the bot | detective | event | screening | ASI01 | LLM01 |
| GD-03 | no answer without evidence | no proof, no answer — hands to a human | detective | private-note | screening | ASI09 | LLM09 |
| GD-04 | inbound text cap | cuts very long customer messages | attestation | config | screening | ASI08 | LLM10 |
| GD-05 | loop breaker | stops the bot replying to itself | detective | private-note | screening | ASI08 | LLM10 |
| GD-06 | turn cap | one question cannot run forever | attestation | config | screening | ASI08 | LLM10 |
| GD-07 | hourly reply cap | caps bot replies per chat per hour | detective | private-note | screening | ASI08 | LLM10 |
| GD-08 | echo direction guard | phone reply copy can never wake the bot | detective | event | screening | ASI09 | LLM06 |
| GD-09 | staff reply guard | the bot never answers your own staff | detective | event | screening | ASI09 | LLM06 |
| VC-01 | voice reply guard | checks every spoken reply before the caller hears it | test | event | screening | ASI05 | LLM05 |
| VC-02 | voice canary | flags risky spoken replies, never blocks them | detective | event | screening | ASI05 | LLM05 |
| VC-03 | voice wallet gate | no money, the number does not answer | test | event | authorization | ASI08 | — |
| VC-04 | voice handover flip | handover moves the call to your staff | detective | event | screening | ASI06 | — |

### GD-01 — sender rate limit

**Claim.** A single sender cannot flood the bot; excess messages are shed without losing real ones.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — one sender exhausting the agent's capacity

Mutation-verified: rate check forced to allow, suite went red. Declared gap: on channels where the flood is blocked before the tenant is resolved, those blocks cannot be attributed and are not counted.

### GD-02 — injection detected

**Claim.** Prompt-injection attempts are detected and recorded.

**Threat.** ASI01 (Agent Goal Hijack) — the classic goal-hijack attempt

Mutation-verified: detector made to never flag, suite went red. Capture migrated from derived (regex re-scan of all stored inbound text on every page load — most of the page's render time) to an event stamped at detection time, with the page counting rows. Declared blind spots: counting began at deploy (a partial first day), customer-service path only, messages merged by the inbound debounce are scanned once, console/test traffic is included, and detection patterns are English-only. The old any-channel scan survives only in frozen daily snapshots.

### GD-03 — no answer without evidence

**Claim.** An agent granted the strict-grounding capability never answers from nothing: a reply built on zero knowledge-base hits and no tool call is rewritten to a handover instead of being sent.

**Threat.** ASI09 (Human Trust Exploitation) — answering from nothing is false confidence

Mutation-verified: guard made to always pass replies, suite went red. Was a real, shipped guardrail with no register entry — found by questioning a numbering gap rather than trusting a string search. Known evidence limit (not an implementation one): the guard rewrites the reply to the handover marker and downstream treats it exactly like a model-initiated handover — same flip, same note wording — so the note proves A handover happened but not that GROUNDING caused it, and the number of ungrounded answers prevented is not separately countable; the guard's own log lines are not queryable evidence. Applies only to agents granted the strict setting, not all.

### GD-04 — inbound text cap

**Claim.** Customer text is capped at a fixed character limit before it reaches the model, the trace, or billing.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — an oversized payload crowding the context window

Mutation-verified. The cap is compile-time with no env override, and deliberately sits above every channel's native message-length limit, so no channel-legal message is ever truncated — it only bites stitched or pasted payloads. Admin/console input is trusted and uncapped by design, which is why this is not a fleet-wide claim about all input. Declared gap: truncation is not recorded, so frequency is unknown.

### GD-05 — loop breaker

**Claim.** Runaway bot loops are broken after a fixed short run of consecutive bot replies with no customer message in between.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — a runaway loop consuming budget and trust

Mutation-verified: verdict forced to ok, guard suite went red. Keys on consecutive bot replies with no inbound between — a human message always breaks the chain.

### GD-06 — turn cap

**Claim.** A single customer question is capped at a fixed number of model turns, so one run cannot loop forever.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — one question looping without end

Prod-read: the env override is unset in production, so the code default applies. Taxonomy note: filed under guardrails rather than alignment on purpose — this is runaway-loop / unbounded-consumption resistance, the same family as the loop breaker; filling a numbering gap in another category would have been the wrong taxonomy. Declared gaps: the limit is server-tunable so the real number may differ, and hitting it is not recorded.

### GD-07 — hourly reply cap

**Claim.** The bot cannot exceed a fixed hourly per-conversation reply cap; past it the AI is muted and staff are asked to take over.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — one conversation burning budget without end

Mutation-verified. Registered late: a guardrail the operator had tuned personally but which was never on the page — they remembered the number and could not find it. The threshold's history is kept deliberately: at a lower value it once muted the bot mid-sale on a talkative but genuine customer, so it was raised — lowering it back is the known regression to avoid. The loop breaker is the real runaway detector; this is a cost/abuse backstop. Declared gaps: counted together with the loop breaker (both leave the same kind of note, so the page cannot tell them apart), the value is server-tunable, and zero turns it off.

### GD-08 — echo direction guard

**Claim.** A coexistence echo (a message the business sent from its own messaging app on the same number) is stored as the business's outgoing reply — it can never be mistaken for a customer message, trigger an AI reply, or flip a human-owned conversation back to the AI; an echo whose sender is not the inbox's own number is dropped and recorded.

**Threat.** ASI09 (Human Trust Exploitation) — the bot answering the business's own staff

Mutation-verified: direction assertion forced false stored both forged and self-consistent forged echoes, tests went red. The echo sender must equal the inbox's STORED own number (with a display-number metadata fallback; an empty value never matches); a mismatch is dropped and stamps a direction-mismatch guardrail event.

### GD-09 — staff reply guard

**Claim.** On the line that delivers staff their alert messages, a reply from a recognised staff member is withheld from the bot while everyone else on that line is served as a customer; a recognition lookup that fails is recorded as its own state rather than counted as a screening, so a blind guard cannot read as a quiet one.

**Threat.** ASI09 (Human Trust Exploitation) — the bot answering the business's own staff

Replaces a blanket 'ignore every message on the alert line' rule that held only while the line had no customers — a real inbox once lost weeks of inbound messages at info log level, looking exactly like silence. Mutation-verified with a designed split: the mutation removed the guard, not the line, so customer-path tests still passed while every staff-protection test failed. Event kinds distinguish caught / could-not-decide / recognition-set-changed, plus a checked counter incremented only on successful reads. Declared gaps: recognition depends on staff numbers being configured; the drop is guaranteed while evidence writes are best-effort; and when the alert channel is off entirely the guard does not run — the checked counter then reads absent rather than zero, the honest signal.

### VC-01 — voice reply guard

**Claim.** No model output is spoken verbatim on a voice call: an exact no-reply sentinel is silenced, and a handover prefix is stripped, its visible line spoken, and the bot muted for the remainder of that call.

**Threat.** ASI05 (Unexpected Code Execution / Unsafe Output) — unvetted model output straight into a caller's ear

Voice controls were registered at build time, per the standing rule that a control which cannot be evidenced is not finished — the gateway declares its missing instrumentation rather than hiding behind a reassuring zero. Mutation-verified at the unit level. Declared gaps: a reply-grounding golden set exists but its runner is not yet wired, so 'test' evidence currently means the unit suite, not the golden set; event emission is fail-open — a database fault under-counts fires without touching the call.

### VC-02 — voice canary

**Claim.** Every reply actually spoken on a voice call is screened log-only for protocol residue, unsafe promises and language mismatch; the canary never blocks or mutates a reply.

**Threat.** ASI05 (Unexpected Code Execution / Unsafe Output) — the log-only screen that notices what the guard cannot

Mutation-verified: residue check removed, unit test went red. Declared gaps: detector consolidation with the text-channel canary remains open — two canaries, two vocabularies, until one shared source exists; emission is fail-open and per-fire.

### VC-03 — voice wallet gate

**Claim.** A zero-balance account's voice line refuses pickup before the greeting, and the check fails OPEN on errors so a billing outage never silences a healthy tenant's calls.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — unmetered calls burning tenant balance

Unproven: exercised live against a local stack (a short call moved the wallet balance; the refusal path was manually forced) but no automated test yet — declared rather than hidden. Refusals emit their own event kind, and the charge side is evidenced by wallet-ledger rows tagged with a voice source.

### VC-04 — voice handover flip

**Claim.** A voice handover deterministically mutes the bot for that call and flips the messaging-side conversation to a human handler via the takeover route — relay-enforced, never a tool call.

**Threat.** ASI06 (Memory & Context Poisoning) — escalation the model asks for but must not control

No verification mode recorded yet. Declared gaps: the warm phone transfer does not exist until the telephony phase, and an unset handover-target setting skips the handler flip with only a log line — the event still fires, so the miss is at least counted.

## Fairness (5)

| ID | Control | In the operator's words | Evidence | Capture | Layer | ASI | OWASP |
|---|---|---|---|---|---|---|---|
| FA-01 | same kit for everyone | every customer gets the same instructions | attestation | config | prompt | — | — |
| FA-02 | no VIP lane | no VIP lane — everyone gets the same bot | test | config | screening | — | — |
| FA-03 | same service any language | same service in any language | attestation | config | screening | — | — |
| FA-04 | language limits are visible | language limits are a visible setting | attestation | config | prompt | — | — |
| FA-05 | blocking is deliberate only | only staff can block a customer | detective | not-instrumented | screening | — | — |

### FA-01 — same kit for everyone

**Claim.** Every customer of an agent gets the same instructions: the same kit files and the same escalation ladder.

Prod-read: a live attestation confirms every active agent has all required kit files. The remaining gap is narrower than not-instrumented: PRESENCE of the required kit files is checked; the escalation ladder inside them is not compared.

### FA-02 — no VIP lane

**Claim.** A customer's tier, name or country never reaches the reply path — a VIP and a first-time customer get the identical bot.

Mutation-verified: injecting a tier reference into the retrieval path made the scan fail. Proven by ABSENCE — a test fails the build if tier/VIP/priority ever appears on the reply path. Declared boundary: marketing campaigns DO segment by tier; that is outreach, not service.

### FA-03 — same service any language

**Claim.** The language is detected per message, so service does not depend on which language the customer writes in.

Mutation-verified: language detection forced to null turned the interceptor suite red. Declared nuance: per-message detection follows a customer switching language mid-chat; answer quality still depends on the knowledge-base content available in that language.

### FA-04 — language limits are visible

**Claim.** A business may restrict which languages it supports, but only through visible settings — never hidden inside the agent's personality.

Prod-read: the languages settings column is present in production, editable and readable. Declared gap: nothing stops a tenant ALSO writing a language rule into their agent files, where it would not show here.

### FA-05 — blocking is deliberate only

**Claim.** The only per-customer difference in service is an explicit staff 'blocked' flag — never a trait the system inferred.

**Declared gap.** Blocking is a deliberate staff action but is not recorded as a safety event, so who was blocked, and when, does not appear on the evidence surface.

Prod-read: the blocked column is present in production; blocked contacts are skipped by the inbound path. Declared gap: blocking is a deliberate staff action but is not recorded as a safety event, so who was blocked, and when, does not appear on the page.

## Review routing (7)

| ID | Control | In the operator's words | Evidence | Capture | Layer | ASI | OWASP |
|---|---|---|---|---|---|---|---|
| RR-01 | handover in code | code hands the chat over, not the bot | detective | private-note | screening | ASI09 | LLM09 |
| RR-02 | re-check before sending | drops the bot reply if staff replied first | detective | not-instrumented | screening | ASI09 | LLM09 |
| RR-03 | one open handover per chat | only one open handover per chat | attestation | config | platform | — | — |
| RR-04 | failed mute surfaced | shouts if the bot fails to go quiet | detective | private-note | screening | ASI08 | LLM09 |
| RR-05 | one alert per conversation | one alert per chat, not per message | attestation | config | platform | ASI08 | — |
| RR-07 | handover SLA | alerts if a waiting customer is left too long | detective | event | platform | — | LLM09 |
| RR-09 | handover auto-reset | idle chats go back to the bot | attestation | config | platform | — | — |

### RR-01 — handover in code

**Claim.** An escalation flips the conversation to a human in CODE, not by asking the model to call a tool.

**Threat.** ASI09 (Human Trust Exploitation) — the model must not merely claim it escalated

Mutation-verified: handover marker made unrecognisable, guard suite went red. Incident drill-through links to an operator-safe conversation viewer that takes the tenant from the URL and filters on both ids; the tenant-facing route is deliberately not reused because it resolves the tenant from the viewer's session and would open the wrong tenant from a cross-tenant page.

### RR-02 — re-check before sending

**Claim.** Conversation ownership is re-checked immediately before sending: if a human took over while the AI was composing, the AI's reply is thrown away.

**Threat.** ASI09 (Human Trust Exploitation) — the bot talking over a human who already replied

**Declared gap.** The discarded reply is logged but not recorded as a safety event, so how often a human was protected from being talked over is unknown.

Unproven: the re-check is inline in the webhook with no exported function, so a unit test cannot reach it without refactoring. Declared gap: the discarded reply is logged but not recorded as a safety event, so how often a human was protected from being talked over is unknown.

### RR-03 — one open handover per chat

**Claim.** The database itself allows only one open human-handling session per conversation, so response-time reporting cannot double-count.

Prod-read: the unique partial index is present in production. Declared limit: it guarantees at most one OPEN session per conversation, not that the session was closed at the right moment.

### RR-04 — failed mute surfaced

**Claim.** When muting the AI after a handover fails, the failure is surfaced loudly rather than leaving a live bot on a handed-over conversation.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — a failed handover must not propagate silently

Mutation-verified: severity downgraded from critical, test went red. The private note is the durable record; a real-time operator ping is layered on top. Design rule: the record is written whether or not the alert was delivered, so a missing alert never means a missing incident — alert DELIVERY itself is log-only, not evidence.

### RR-05 — one alert per conversation

**Claim.** Staff get one alert per conversation, not one per message — and an escalation always alerts regardless.

**Threat.** ASI08 (Cascading Failure / Resource Overload) — an alert storm trains staff to ignore alerts

Mutation-verified: dedup forced to always allow, tests went red. Declared gap: the dedup lives in memory, so a restart can allow one repeat alert. Escalations bypass the dedup deliberately — they are never suppressed.

### RR-07 — handover SLA

**Claim.** After a human takes a conversation over, a customer left waiting past the SLA raises a staff alert, and the breach is recorded even when no alert could be delivered.

Mutation-verified. Measurement basis matters: the wait is measured from the HANDOVER, not the customer's last message — measuring from the message once recorded an absurd multi-day 'breach' seconds after someone took over a stale conversation; nobody can answer a message before they own it. Rows carrying the old basis predate the handover timestamp and may include time before anyone was responsible. Declared gaps: only handovers after the feature shipped can be measured fairly, and the alert has nowhere to go until a staff notification channel is configured.

### RR-09 — handover auto-reset

**Claim.** A conversation handed to humans and then left idle returns to the AI automatically after a fixed idle window rather than stalling forever.

Unproven: no test covers the idle-reset constant.

## Compliance (10)

| ID | Control | In the operator's words | Evidence | Capture | Layer | ASI | OWASP |
|---|---|---|---|---|---|---|---|
| CP-01 | session memory retention | old chat memory is deleted on schedule | attestation | not-instrumented | platform | ASI06 | LLM06 |
| CP-02 | backups encrypted | backups are encrypted | attestation | not-instrumented | platform | — | LLM06 |
| CP-03 | phone masked in logs | logs show only the last few digits | attestation | config | platform | — | LLM06 |
| CP-05 | admin 2FA | admin logins need a second factor | attestation | config | authorization | — | LLM06 |
| CP-06 | one session per login | a new device signs you out everywhere else | attestation | config | authorization | ASI03 | LLM06 |
| CP-07 | staff notes stay internal | private notes never reach customers or the bot | attestation | config | screening | ASI06 | LLM06 |
| CP-08 | backups checked and pruned | backups are tested, old ones deleted | attestation | config | platform | — | LLM06 |
| CP-09 | admin-only screens | billing and settings are admin-only | attestation | config | authorization | ASI03 | LLM06 |
| CP-10 | scheduled jobs run | a job that stops running shows up | detective | derived | platform | — | LLM06 |
| CP-11 | critical events page someone | serious problems reach a real person | attestation | config | platform | — | LLM06 |

### CP-01 — session memory retention

**Claim.** Conversation session memory is deleted on a fixed retention schedule.

**Threat.** ASI06 (Memory & Context Poisoning) — stale memory re-teaching old mistakes

**Declared gap.** The retention value lives in another service's environment, which the attesting service cannot read to prove it.

Prod-read: the retention window is set in the production environment. Declared gap: the retention value lives in the other service's environment, which the attesting service cannot read to prove it.

### CP-02 — backups encrypted

**Claim.** Database backups are encrypted at rest.

**Declared gap.** Encryption only happens when a passphrase is configured; without one, backups are plain compressed dumps.

The declared-failure pattern applies here: an unencrypted-backups state is worth flagging with the failing flag rather than describing in prose, because a renderer cannot see prose — and a compliance page that groups a broken control with healthy ones reads as an all-clear.

### CP-03 — phone masked in logs

**Claim.** A customer's phone number appears in logs only as a masked suffix (last few digits).

Mutation-verified: mask made to return the full number, suite went red. Registered together with the fix itself, per the standing rule — the claim had been made for months while multiple log sites wrote full numbers. Masking is unconditional, with no env flag. Declared gaps: proven by tests, not a live check; covers logs only — traces in the tracing platform keep the full number by deliberate operator decision.

### CP-05 — admin 2FA

**Claim.** Platform super-admin accounts require a second factor.

A dated point-in-time snapshot sitting beside a LIVE attestation on the same screen can disagree with it; the live reading is authoritative and the snapshot is marked historical, because an evidence page that contradicts itself teaches the reader to trust neither number. Also the register-first rule applied backwards: an attestation existed for a control the register did not define, which put an unexplained row on the coverage page.

### CP-06 — one session per login

**Claim.** Logging in on a new device signs the account out everywhere else.

**Threat.** ASI03 (Privilege Abuse) — a stolen old session must stop working

Prod-read: login rotates the stored access token, which the JWT session id is checked against. Declared gaps: applies to tenant staff logins; session takeovers are not recorded, so the page cannot show how often it happened.

### CP-07 — staff notes stay internal

**Claim.** Staff-only private notes are never shown to a customer and never fed to the AI.

**Threat.** ASI06 (Memory & Context Poisoning) — internal notes must not become AI context or customer text

Unproven: no test covers private notes being withheld from the agent. Declared gap: covers the customer-service path; a note remains visible to any staff member with access to the conversation.

### CP-08 — backups checked and pruned

**Claim.** Every backup is verified readable before it is kept, and copies older than the retention window are deleted.

Prod-read: backup files are present and pruned by retention. Declared gaps: the integrity check proves the file is readable, not that a full restore works; encryption is a separate control, and that one is currently off.

### CP-09 — admin-only screens

**Claim.** Billing, reports and connection settings are admin-only; ordinary staff are refused.

**Threat.** ASI03 (Privilege Abuse) — ordinary staff must not reach billing or settings

Mutation-verified: role gate forced to pass everyone, suite went red. Declared gap: refusals are not recorded, so attempted access does not appear on the page.

### CP-10 — scheduled jobs run

**Claim.** Every scheduled job records each run, and a job that stops firing becomes visible without anyone looking.

Mutation-verified against a real scheduler-library gotcha (its previous-run call is always undefined off a scheduled instance — the mutation made every cron silently un-overdue-able). Evidence is DERIVED from the job-run table, not the guardrail event stream, deliberately: the event table is tenant-scoped with a non-null tenant FK and these are platform jobs with no tenant to attribute to, so the insert would throw exactly when an alert matters. Declared gaps: the operator-alert throttle is at-most-once-per-interval and in-memory, so it does not survive a restart; and the monitor runs INSIDE the service it monitors — if that service is down, nothing here reports. An external dead man's switch is the named fix and is not in place.

### CP-11 — critical events page someone

**Claim.** A critical guardrail event reaches an operator who can act on it.

The last hop is the one that fails: events can be emitted and routed correctly, then delivered to an operator channel that is not configured — and that failure affects every producer of critical severity at once. Route platform-internal alerts to an operator-owned channel, never to a tenant account that happens to have a working channel: that would leak operational detail and page people who cannot act. A gap may be declared, but never left undeclared.

