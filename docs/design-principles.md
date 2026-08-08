# Design principles for AI safety rails

Twenty principles and fifteen mechanism patterns, extracted from the production
system behind this framework. Each mechanism records the direction it fails in
— open or closed — because that choice, made deliberately per layer, is most of
the design.

## Principles

1. Absent is never zero (and never a perfect score): not-instrumented, never-run, gate-absent, and not-observable are all first-class rendered states, because measured-and-clean and never-measured must not look alike, and the safest-looking default is usually the lie.
2. Enforce in code, never in the prompt: a convention the model must remember on every line will eventually be dropped, while a replace() or a relay-side state flip cannot forget — use prompts to instruct and code to enforce.
3. Escalation is deterministic and relay-owned: the model only signals intent with a fixed marker; the surrounding code performs the actual state change, so 'the escalation tool never fired' can never happen again.
4. Choose each layer's failure direction by naming the worse silent failure: guards protecting answer correctness fail closed (escalate rather than answer), while limiters, billing gates, and telemetry fail open (never silence a real customer over an infrastructure hiccup) — and every fail-open is paired with compensating bounds or a loud escalating alarm.
5. Observability must be structurally unable to break what it observes: fire-and-forget, never awaited on the serve path, bounded buffers, never throws — a reporting outage must not become a customer outage.
6. Evidence classes are not interchangeable: attestation proves a control is armed, detective events prove it fired, tests prove it still works — a control that never fired is indistinguishable from one switched off without all three.
7. Count the looking, not just the catching: record that every output was screened so a quiet week is distinguishable from a dead detector.
8. Latest means latest attempt, not latest success: a broken run must displace a previous pass in the headline, or the surface reports PASS for a suite failing every night since.
9. Declare the register in code and compare against run records at read time: discovery from evidence can only show things that work, and a watchdog job watching for missing jobs would share their exact failure mode.
10. One definition, many consumers: critical severity tuples, severity/label mappings, schedule resolution, and shared detectors each live in exactly one exported place, because a drifted copy silently stops paging, contradicts itself on one screen, or lets live rails and evals diverge.
11. Evidence carries labels, never payloads: derived phrases instead of message bodies and truncated identifiers keep the evidence store from becoming a second copy of customer data with the same privacy duties.
12. Signals that trigger critical responses must be unforgeable: match the full canonical machine-written sentence, never a prefix that user- or model-steerable text could reproduce.
13. Ship detection before enforcement: run a new guard in warn-only mode, measure its false-positive rate on live traffic, and only then let it block — especially when a false fire mutes the product for a whole conversation.
14. A false alarm on a critical surface is itself a safety failure: a job rendered red every day while running fine, or working controls counted as warnings, trains the operator to ignore the color — so controls-working events count as info, disabled jobs are never called overdue, and lateness is never asserted on a guess.
15. Everything on a hot path is bounded: input length, buffers, batch sizes, throttle maps, lookbacks — and when the bound is hit, the drop is counted and logged rather than silent.
16. Refuse rather than clamp operator input, and name the consequence in the refusal: silently rounding an override leaves the operator believing something the system is not doing, and a refusal without a reason gets the bound edited next.
17. Distrust model output as thoroughly as user input: URLs, markers, and formatting the model emits are allow-listed, parsed, or normalized in code before anything acts on them.
18. Anomaly thresholds need a ratio AND an absolute floor: small baselines jump many-fold on tiny numbers, and a self-relative check alone false-fires on exactly the accounts least able to interpret it.
19. Keep decision logic pure and I/O-free so every rendering and suppression rule is exhaustively unit-tested instead of discovered in production against real data.
20. When a cap false-fires on a real user, raise it rather than remove it: the guard's existence is the lesson of one incident, its level is the lesson of another, and both must survive the fix.

## Mechanism patterns

Each entry: what the mechanism does, which way it fails and why that direction
was chosen, and the reusable pattern.

### Reply guard (output protocol)

Declares a deterministic output protocol for the LLM: an exact sentinel token means 'send nothing', and an escalation marker prefix means 'send the visible line, then the RELAY flips the conversation to a human'. The relay code, not the model, executes both. It also suppresses pipeline-meta leakage (the model narrating 'do not send a reply' to the customer), strips protocol residue, unwraps quote-copied markers, normalizes markdown bold to the channel's native syntax in code, and allow-lists any media URL the model emits before forwarding it.

**Fail direction.** Fails closed toward suppression: ambiguous protocol residue is treated as protocol and never relayed, because the incident that created this guard was internal meta text reaching customers. But suppression rules are anchored/whole-output so ordinary prose can never trip them — the design explicitly balances the two silent failures (leaking meta text vs. suppressing a legitimate reply).

**Pattern.** Never relay model output verbatim. Give the model a tiny fixed vocabulary for control decisions (silence sentinel, escalation marker) and have deterministic relay code parse and enforce them — no tool call required, so escalation cannot 'not fire'. Treat everything the model writes as untrusted: allow-list any URL it asks you to fetch or forward, and fix formatting conventions with a replace() rather than a prompt rule, because a rule the model must remember on every line will eventually be dropped while code cannot forget.

### Grounding guard

A post-generation backstop for agents flagged 'strict': if a reply was produced with zero knowledge-base hits, no successful tool call, and no pre-fetched facts, the draft is rewritten to the escalation marker plus a language-matched handover line, so it escalates exactly like a model-initiated handover and the ungrounded draft is never sent. Social messages (greetings/thanks) are exempted via a deterministic lexicon fast-path plus a one-word LLM classifier for ambiguous cases. A separate link check flags URLs absent from everything that grounded the turn.

**Fail direction.** Fails closed on every uncertainty: classifier error or timeout, missing retrieval metadata, and degraded retrieval all escalate rather than answer — a wrong answer to a customer is the worse failure. The one deliberate exception is the social exemption, which exists because a false fire mutes the bot for the whole conversation; and new checks (link grounding) start as warn-log-only and are flipped to enforcement only after the false-positive rate has been measured on live logs.

**Pattern.** Check that a reply is SUPPORTED, not merely that retrieval returned something — retrieval presence is not support for what was said. Count only tool calls that returned without error as grounding (an emitted call is not an answered call, or the guard switches itself off during a data-source outage, exactly when it is needed). Route the rewrite through the same escalation path the model would use, so one relay behavior covers both origins. When a guard's false fire is expensive, ship it in observe-only mode first and enforce from measured data.

### Reply canary (log-only screening)

Runs the same detectors the eval suite trusts (unsafe first-person money-back promise, protocol-token residue, cross-script language mismatch) on every reply actually relayed to a customer, and logs loudly on a hit. It records that every reply was checked — not just the hits — so a quiet week is distinguishable from a dead detector, and stamps hits as durable evidence events at detection time.

**Fail direction.** Fails open, absolutely: it never blocks or mutates the reply, and its own errors are caught and logged. A false positive must cost a log line, not a customer answer — enforcement lives in other layers; this layer exists to shrink the days-long gap between a bad reply shipping and a human noticing.

**Pattern.** Put a passive canary on the live output path running the exact detectors your offline evals use, imported from one shared module so the live rail and the eval suite cannot drift. Record the looking as well as the catching ('checked N, caught 0'), and stamp evidence rows at detection time rather than re-deriving them by scanning history at read time. Match detectors conservatively: a detector that cries wolf makes its own metric untrustworthy.

### Per-sender rate limiter

A fixed short window in a shared store, keyed per sender per channel — deliberately not per IP, because platform webhooks all arrive from the platform's egress addresses, so an IP limit would throttle the platform rather than the abusive sender. Over-limit messages are dropped while returning a success acknowledgment to the platform, because a non-2xx triggers platform redelivery, which would amplify the very flood being shed.

**Fail direction.** Fails open on store errors: a broken limiter must never silence real customers. That is safe only because other independent layers still bound the damage — per-sender processing locks bound concurrency and the inbound text cap bounds per-message cost — so the fail-open choice is made with named compensating controls, not hope.

**Pattern.** Key rate limits on the identity that actually misbehaves, not the network path the traffic arrives on. Distinguish deliberate drops (acknowledge success so the platform does not redeliver) from transient failures (return an error so the message IS redelivered) — the response code is a retry-semantics decision, not a status report. Fail open only where you can name the other layers that still bound the blast radius, and throttle your own warning logs so the flood does not also flood your logging.

### Inbound input cap

Caps untrusted customer-origin text at every entry point BEFORE it reaches the model, the trace store, and billing — one bounded message everywhere. The cap is set above every channel's native message-length limit, so no channel-legal message is ever truncated; it only bites artificially stitched or pasted oversized payloads. Trusted admin/console input is deliberately uncapped.

**Fail direction.** Fails closed by construction — it is a pure, deterministic truncation with an explicit truncation marker, so there is no error path. The direction chosen is 'always bounded': an unbounded paste can crowd the context window and inflate cost invisibly.

**Pattern.** Bound untrusted input once, at the entry point, before it fans out to model, telemetry, and billing — capping downstream in one consumer leaves the others unbounded. Choose the bound above the largest legitimately-possible input so the cap can never harm a real user, and append a visible marker so truncation is observable rather than silent. Distinguish trust levels: the same cap that protects against hostile input would break legitimate trusted workflows.

### Injection-attempt tagger

Phrase-heuristic detection of prompt-injection attempts ('ignore your instructions', 'reveal your system prompt', role-override, jailbreak-mode phrasing) that only TAGS the message for metrics and tracing — it never blocks. It strips the channel envelope header before matching, because some channels put user-controlled display names in that header and a hostile display name would otherwise false-positive every message from that user and pollute the metric.

**Fail direction.** Fails open by design — it is observability, not enforcement. Blocking on phrase heuristics would lock out real customers on false positives; actual containment is the deny-by-default tool lockdown and server-side tenant isolation, which hold regardless of whether the attempt was detected. A match is a signal; absence is explicitly not proof of innocence.

**Pattern.** Separate containment from detection. Contain injection with capability restriction (deny-by-default tools, server-side identity that model input cannot override) so an undetected attack still fails; use cheap heuristic detection purely to make attack pressure measurable, so screening can later be tightened with data instead of guesswork. Run detection on the actual untrusted text, stripped of any envelope your own pipeline added, or attacker-controlled metadata corrupts the metric.

### Fail-open evidence emitter

The single channel through which hot-path guardrail fires become durable evidence rows in another service. It never throws, is never awaited by the reply path, batches events on a short timer, bounds its buffer, and under sustained pressure drops evidence with a throttled warning rather than growing memory. It carries only a kind, a reason code, and structured non-PII detail — never message or reply text. The one critical-severity event (escalation succeeded but muting the AI failed) is defined in exactly one exported function because four different relay paths reach that state and four hand-written copies of the severity tuple would drift.

**Fail direction.** Fails open, absolutely: observability that can break the thing it observes is worse than no observability, because it converts a reporting outage into a customer outage. Every drop is counted and logged, so lost evidence is a known quantity rather than a silent one.

**Pattern.** Make the telemetry write path structurally incapable of harming the serve path: fire-and-forget, bounded buffer, batched flush, timers that never hold the process open, and a catch-all so it can never raise. Keep payloads out — an evidence log that contains customer text becomes a second copy of customer data with all the same retention and privacy duties. Define each alert-worthy severity tuple in one function so multiple call sites cannot drift, because a downgraded copy silently stops paging anyone.

### Loop breaker (bot reply guard)

A pure decision function evaluated where bot replies are stored before delivery. Three rules: identical replies within a short window are dropped as duplicates (the window matters — the same answer to the same question a day later is legitimate); a small number of consecutive bot replies with no inbound customer message between them is the primary runaway signal (a bot-to-bot echo never waits for a human, so it trips in seconds, while a genuine customer cannot trip it at all); and a generous hourly cap is a cost backstop only, deliberately set well above a talkative-but-real conversation after a tighter cap once muted a real customer mid-purchase. Runaway drops the reply AND flips the conversation to a human.

**Fail direction.** Fails closed on runaway — drop and mute so a human looks — because unbounded loops burn money and look broken. But paths that store a message only AFTER delivery are deliberately left unguarded: the message already reached the customer, so hiding the record from staff would be worse than the duplicate. The fail direction is chosen per call site by asking what state the outside world is already in.

**Pattern.** Prefer structural loop signals over volume thresholds: 'N automated replies with no human turn between them' cannot be tripped by a legitimate user and catches echo loops in seconds, whereas a volume cap will eventually silence a real conversation. Keep a volume cap only as a backstop, tuned from the real distribution — and when it false-fires on a real customer, raise it rather than remove it. Keep the decision layer pure and I/O-free so it is exhaustively unit-testable.

### Nightly guardrail scan (monitor by exception)

A nightly cron that re-runs the exact detection queries once used to scope a real incident, over the trailing day, and notifies each affected account's staff channels. It deliberately hunts for BYPASSES of the other guards: leak patterns the reply guard should have suppressed appearing in delivered messages, escalations whose AI-mute failed, per-conversation reply volume the loop breaker should have made impossible, and token-burn anomalies (a ratio against the account's own recent daily average AND an absolute floor, because small accounts jump many-fold on tiny numbers). Silent when everything is clean.

**Fail direction.** Fails open operationally: the scan never throws, a malformed schedule disables the scan with a loud log instead of crash-looping the messaging service, and its run-recording proves it RAN, not that it was right. An optional monitor must never take down the product it monitors; its own absence is separately watched by the job register.

**Pattern.** After any incident, freeze the queries used to scope it into a scheduled sweep — each guard's nightly check should ask 'did anything get past the corresponding inline guard?', making the scan an independent second layer rather than a re-run of the first. Alert by exception, aggregate per affected owner, and use ratio-plus-floor for anomaly thresholds so small baselines cannot false-fire. Accept that the sweep proves execution, not correctness, and record both facts separately.

### Attestation (armed-state evidence)

Point-in-time checks that each safety control is CONFIGURED ON right now — config equality across agents, second-factor enrollment on privileged accounts, compile-time constants — as a distinct evidence class from event counts, because a control that has never fired is indistinguishable from one that is switched off unless its state can be read. Controls whose state lives in another service or host are returned as 'not observable' with the reason, never as a green tick or a silent omission, and the module exports the closed list of control ids it attests at all, so 'the read failed' and 'nothing ever reads this' are distinguishable states.

**Fail direction.** Fails closed toward honesty: a check that errors returns not-observable with a reason, never a pass; an expected-to-fail control is surfaced with its real number rather than hidden. Claiming to have verified something you cannot see is exactly the audit failure this class exists to prevent.

**Pattern.** Split 'is it armed?' from 'did it fire?'. For each control, either read its live state mechanically or explicitly declare it unobservable from here with the reason — never guess, never default green. Publish the roster of what is attested at all, keep it adjacent to the loader, and pin them together with a test so a new attestation cannot be added without the roster noticing. Snapshot attestations daily so 'was this control on during that quarter?' has an answer.

### Detective evidence reader

The read side of guardrail evidence: aggregates durable event rows and byte-stable prefixed private notes into per-owner counts, category rollups, a paginated incident feed, and an export pack. Controls with no instrumentation report 'not instrumented' — never zero. The critical signal is matched on its full canonical machine-written sentence, not a forgeable prefix, because other writers emit similarly-prefixed notes with model-authored text, and a steerable string must not be able to light the critical lamp. Feed labels are derived phrases, never note bodies, because note bodies embed customer text.

**Fail direction.** Fails closed toward under-claiming: unknown event kinds attribute to a dash rather than a fallback control (misattributed evidence is worse than unattributed), a category whose evidence lives outside the counting pipeline reports 'not instrumented' rather than computing a false zero-and-OK, and measured-and-clean is never allowed to look like never-measured.

**Pattern.** Keep one severity/label mapping shared between the SQL and the aggregation code so two views of one screen cannot contradict each other, and derive display labels rather than projecting stored content, so evidence surfaces and exports cannot carry customer text out of the system. Match machine-written signal strings on their full fixed sentence so nothing steerable by user or model input can forge a critical signal. Count events where a control WORKED (drops, denials, suppressions) as informational, not warnings — a healthy system that looks sick trains people to ignore the page.

### Eval evidence (test-class) reader

Reads eval-suite results out of durable rows pushed by each harness, joined against a declared register of suites. Two hard rules: a gate with zero scored items renders the literal words 'GATE ABSENT' and never a number (schema-enforced with value-NULL ⇔ denominator-zero, so no renderer default can undo it, since an absent score is byte-identical to a perfect one); and 'latest' means latest ATTEMPT, not latest success, so a broken run displaces a previous pass in the headline. A sweep marks runs that started and never finished as BROKEN, because permanently-pending is indistinguishable from healthy at a glance.

**Fail direction.** Fails closed toward 'absence is a finding': no runner, never run, stale, and broken are all first-class rendered states, and suites with no rows stay in the output. Picking the newest green run — the obvious implementation — is how a surface reports PASS for a suite that has failed every night since, which is failure in the direction of false assurance.

**Pattern.** Push eval results into your own durable store rather than polling a CI system whose 'success' may not mean the assertions passed. Enforce absence-is-not-perfection at the schema level, not the renderer. Derive state from the latest attempt, declare freshness budgets per suite so a pass can go stale, and sweep abandoned in-progress runs to an explicit broken state on a timer.

### Critical-event operator alerting

Real-time paging on the one event class that needs a human immediately, aimed at the operator who can act rather than the tenant who cannot. Throttled per (owner, event-kind) with a fixed window; suppressed alerts are counted and the count rides along in the next alert that gets through ('+N more suppressed'), so a throttled burst cannot be misread as a single event. When a critical alert reaches zero configured channels, it logs at error level, because silence there looks identical to 'no events'.

**Fail direction.** Fails open in two deliberate directions: alerting is fire-and-forget so a notification failure can never fail the ingest that recorded the evidence (the evidence is the more durable half), and the in-memory throttle prefers duplicate alerts after a restart over ever dropping a genuine first alert — when the throttle map is full it evicts the oldest entry rather than refusing to alert, because losing throttle state is recoverable and losing an alert is not.

**Pattern.** Route alerts to whoever can act, throttle per (owner, kind), and make the throttle report its own suppressions — a throttle that hides them turns '1 alert' into '1 event'. Decide the failure direction of every alerting component by comparing recoverable versus unrecoverable losses: duplicates are recoverable, dropped alerts are not. Reuse an existing delivery path instead of building a parallel alerting stack, and treat 'delivered to zero channels' as its own loud failure.

### Scheduled-job register

A code-declared register of every cron and interval job whose silence is an operational or safety problem — the 'should' — compared at page-read time against a run-record table — the 'did'. Discovery from run records can only ever show jobs that work; the register exists so a job that has NEVER reported is the most visible thing on the page. Each job declares its timezone (which travels with the spec), a grace window sized to its scheduler's real drift, a one-line 'what breaks if this stops', an explicit side-effect warning for the run-now button, and legal min/max interval bounds for operator overrides — which are refused with the consequence named, never silently clamped.

**Fail direction.** Fails toward showing bad news: never-run is a rendered state (never a blank or a tick), a start with no finish becomes DIED once past grace, deliberately-disabled jobs show their reason instead of rendering falsely overdue forever, and rows sort worst-first because an operator who must scroll to find the red row stops checking the page. The single softening: a malformed schedule produces no expectation rather than a guess, because a job must never be called overdue on a guess — a false alarm on a critical job teaches the operator to ignore the color.

**Pattern.** Declare what should run in code, record what did run in data, and compute health as the comparison at read time — a watchdog cron that watched for missing crons would share their exact failure mode. Make every non-reporting state (never, died, overdue, disabled) explicit and distinct, carry timezone with each schedule, size grace windows from the scheduler's documented drift, and resolve the effective schedule in exactly one function that the runner, the API, and the page all call so they cannot disagree.

### Prepaid balance gate

Checks the tenant's balance is positive BEFORE each AI run and charges actual token usage AFTER it completes — so the turn that crosses zero still answers and the balance may dip slightly negative; the next turn is blocked. All money math lives in the billing service; this module only reports token counts. A consecutive-failure counter across both the check and the charge escalates to an error-level alert past a threshold, because sustained charge failure is unbounded revenue loss and must not stay a per-call warning.

**Fail direction.** Fails open on network errors — the customer is served and the check returns allowed — because a billing-service hiccup must never silence the product for paying customers; losing a few turns of revenue is recoverable, a customer talking to a dead bot is not. The fail-open is bounded by the circuit-breaker-style alarm: fail open, but scream after N consecutive failures so a systemic outage cannot hide inside per-call noise.

**Pattern.** For usage billing where cost is only known after the fact, gate on 'balance positive before' and charge 'actual after', accepting one turn of overshoot as the price of never blocking mid-conversation. When a gate fails open by design, pair it with a consecutive-failure counter that escalates loudly at a threshold — silent fail-open is indistinguishable from nobody paying. Keep money math in one owning service; satellites report quantities only.

