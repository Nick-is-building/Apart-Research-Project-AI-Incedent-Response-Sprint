# Paper tables

**Generated file — do not edit by hand.** Every figure in it is read from `data/` or computed by `src/`. Regenerate with `python3 src/paper_tables.py`, or run `./verify.sh` to rebuild the whole pipeline and check the reference values.

Generated 2026-09-14. Sources are cited by the short codes registered in `data/sources.csv`; the full evidence base is `docs/belegbasis-v3.md`.

**Notation:** always `P_wall` (calendar time) or `P_exp` (agent exposure time), never a bare `P` — in the security and verification literature `P` regularly denotes a probability.

---

## Table 1 — The clock

One row per control. `P_wall` is computed by `src/compute_p.py`, never entered by hand.
Type C rows are pre-existing controls: no application event, therefore no `P_wall`.

| id | type | control | protection goal | goal source | applied (UTC) | reconstituted (UTC) | `P_wall` | state | category | status |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | A | Blocking of the vulnerable token API routes and revocation of shared re… | No evaluation workload reaches the external internet, by any ro… | operator | 2026-07-06T01:16Z | 2026-07-08T00:06Z | 46 h 50 min | bypassed | K1_alternative | PRIMARY |
| A2 | A | Same Artifactory rebuild measure - state-erasing wipe of the unintended… | Agents can no longer pass notes to one another | assumption | 2026-07-06T01:16Z | 2026-07-08T16:01Z | 62 h 45 min | bypassed | K2_training | PRIMARY |
| A3 | A | Same Artifactory rebuild measure - mitigation of the reader-to-admin ex… | No agent holds Artifactory administrator privileges | operator | 2026-07-06T01:16Z | 2026-07-13T08:46Z | 175 h 30 min | bypassed | K1_alternative | PRIMARY |
| C1 | C | URL allowlist of the `datasets` library | Prevent the worker from acting on attacker-determined external… | operator | PRE_EXISTING | NOT_DATED | — | held | K1_alternative | PRIMARY |
| C2 | C | Hub production database behind a private link with address allowlist | The agent does not reach the Hub production database | assumption | PRE_EXISTING | NEVER | — | held | none | PRIMARY |
| C3 | C | IAM policy on node-role replay | A replayed node role yields no control over the environment | assumption | PRE_EXISTING | NEVER | — | held | none | PRIMARY |
| C4 | C | Credential store and cluster keys | No agent obtains credentials or cluster keys from the store | assumption | PRE_EXISTING | NEVER | — | held | none | PRIMARY |
| C5 | C | CI execution policies | No agent-authored change reaches production | assumption | PRE_EXISTING | NEVER | — | held | none | PRIMARY |
| C6 | C | Kubernetes restrictions towards GPT-5.6 Sol | The agent gains neither cluster-wide visibility nor secrets | assumption | PRE_EXISTING | NEVER | — | held | none | PRIMARY |
| C7 | C | Administrator threshold on anonymous tokens | An anonymous token never yields administrator privileges | assumption | PRE_EXISTING | NEVER | — | held | none | PRIMARY |
| C8 | C | Host-mount restriction | No workload obtains access to the node file system via a host m… | assumption | PRE_EXISTING | NOT_DATED | — | broken ¹ | unclassified | PRIMARY |
| C9 | C | Correlating detection stack at Hugging Face | Raise the alert's criticality and trigger the on-call team | operator | PRE_EXISTING | NOT_DATED | — | fired_not_escalated | K4_escalation | PRIMARY |
| C10 | C | Egress throttling | Prevent effective data transfer out of the sandbox | assumption | PRE_EXISTING | NOT_DATED | — | bypassed | K1_alternative | PRIMARY |
| C11 | C | DNS resolution | Prevent the workload from reaching hosts outside the permitted… | assumption | PRE_EXISTING | NOT_DATED | — | bypassed | K1_alternative | PRIMARY |
| C12 | C | Intermittent egress blocks | Prevent the workload from reaching external hosts | assumption | PRE_EXISTING | NOT_DATED | — | bypassed | K1_alternative | PRIMARY |
| C13 | C | Blocking of direct outbound connections | Prevent the workload from reaching external hosts | assumption | PRE_EXISTING | NOT_DATED | — | bypassed | K1_alternative | PRIMARY |
| C14 | C | No TUN device in the sandbox | Prevent the workload from building a tunnelled network path out… | assumption | PRE_EXISTING | NOT_DATED | — | bypassed | K1_alternative | PRIMARY |
| C15 | C | OpenAI outbound network controls | No internet access out of the evaluation environment | operator | PRE_EXISTING | NOT_DATED | — | bypassed | K1_alternative | PRIMARY |
| C16 | C | Integrity of the Artifactory container image cache | A workload resolving an image reference receives the trusted im… | assumption | PRE_EXISTING | NEVER | — | defeated_no_effect | none | PRIMARY |
| X1 | X | Network restrictions on access to GitHub (UK AISI cyber range) | The agent does not reach GitHub from the evaluation environment | assumption | PRE_EXISTING | NOT_DATED | — | bypassed | K1_alternative | PRIMARY |
| X2 | X | Harness write block against the public wiki (Nightingale / DseWiki) | The agent does not write to public wikis | assumption | PRE_EXISTING | NOT_DATED | — | held | K1_alternative | SECONDARY |
| X3 | X | Web access restriction on evaluation agents | Prevent agents from retrieving data from the public web | operator | PRE_EXISTING | NOT_DATED | — | bypassed | K1_alternative | SECONDARY |

¹ C8: the state is **not determinable from the source**. P1 records only that the first privileged host-mount pod failed and that a second succeeded minutes later, without describing the difference, so the distinction between a defeated control and a circumvented one cannot be made. `broken` is the recorded value but is as much a claim as `bypassed` would be. This is the only such row in the corpus.

---

## Table 2 — Corpus breakdown by row type and state

The corpus contains exactly one control-application event: the Artifactory rebuild of `2026-07-06T01:16Z`. Every other control in it was already standing, which is why type B is defined in the schema and empty in the data.

| row type | n | broken | bypassed | defeated no effect | fired not escalated | held | with `P_wall` |
|---|---|---|---|---|---|---|---|
| A — applied, nested | 3 | 0 | 3 | 0 | 0 | 0 | 3 |
| B — applied, not nested | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C — pre-existing | 16 | 1 | 6 | 1 | 1 | 7 | 0 |
| X — out of corpus | 3 | 0 | 2 | 0 | 0 | 1 | 0 |
| **Total** | **22** | **1** | **11** | **1** | **1** | **8** | **3** |

---

## Table 3 — The four calculations

### 3a — Declared response budget against measured performance

| quantity | value | source |
|---|---|---|
| Alert | 2026-07-19 12:03 UTC | P1 section X |
| Runs stopped | 2026-07-19 17:37 UTC | P1 section X |
| Measured | 5 h 34 min = 334 min | computed |
| Declared: window to a pause | 30 min | OpenAI, 2026-08-18; evidence base 14 |
| Declared: full sequential chain | 60 min | OpenAI, 2026-08-18; evidence base 14 |
| **Factor over the pause window** | **11.1×** | computed |
| **Factor over the full chain** | **5.6×** | computed |

Two precision points travel with this number. **First**, the budget was declared on 18 August 2026, *after* the incident, so it is not a broken promise but a target calibrated against a performance the organisation has never demonstrated. **Second**, the 30-minute figure is *older* than the August commitment: P19 of 19 March 2026 already describes review within 30 minutes of completion, with escalation to human review inside 30 minutes. What the August commitment adds is the move from **asynchronous review to blocking intervention, not the interval** — OpenAI's own March text notes that extending to synchronous blocking would allow actions to be prevented before execution rather than alerted on shortly after. Presenting 30 minutes as a new safeguard overstates it (evidence base 15.4).

### 3b — UK AISI comparison: two latencies, not one

| organisation | detection latency | reaction latency | source |
|---|---|---|---|
| UK AISI | 11 h 41 min (701 min) | 0 h 46 min (46 min) | P10 section 3 |
| OpenAI | not computable — no start point in the public record | 5 h 34 min (334 min) | P1 section X |
| **Ratio, reaction** | — | **7.3×** | computed |

The two organisations fail at different legs. A `P` budget must declare both, or the failure only moves.

### 3c — Cadence arithmetic

CSA AICM AIS-13 requires review of sandboxing policies *at least annually* = 8,766 hours (evidence base 12.5).

| id | control | `P_wall` | ratio to the prescribed cadence |
|---|---|---|---|
| A1 | Blocking of the vulnerable token API routes and revocat… | 46.8333 h | **187.2×** |
| A2 | Same Artifactory rebuild measure - state-erasing wipe o… | 62.7500 h | **139.7×** |
| A3 | Same Artifactory rebuild measure - mitigation of the re… | 175.5000 h | **49.9×** |

### 3d — The awareness clock

> **What 'breached' means here.** `days` is the interval from the awareness reading to **public disclosure**. That is a *different quantity* from the regulatory obligation, which is discharged by reporting to a regulator, not by publishing. A non-public report to the Commission or to Cal OES could have been timely on any of these readings. Public disclosure is simply the only date the record supplies, so it is the only interval that can be computed.

| awareness reading | date | days to disclosure | EU (5 d) | California (15 d) | evidence | status |
|---|---|---|---|---|---|---|
| 20 Jul - the two incidents are linked | 2026-07-20 | 1 | met | met | P1, P2 | PRIMARY |
| 18/19 Jul - staff find the escape in own logs | 2026-07-18 / 2026-07-19 | 2-3 | met | met | Reuters | SECONDARY |
| 9 Jul - agent bypasses outbound controls | 2026-07-09 | 12 | BREACHED by 7 d | met | P1 IV.A | PRIMARY |
| 5 Jul - security incident opened | 2026-07-05 | 16 | BREACHED by 11 d | BREACHED by 1 d | P1 III.B | PRIMARY |

The 18/19 July reading is carried as a **range** because the source gives one.

**The interpretive question, which is not resolved here:** does the clock start when OpenAI learned that its model had left containment — or only when it learned *whom* the escaped model had hit? The source supports at least three different awareness dates, and which one governs decides a legal question in two jurisdictions. The ambiguity is the finding (evidence base 16.2).

---

## Table 4 — The gap, instrument by instrument

**11 instruments where the absence of a time axis for containment was established by term count, and 6 more by qualitative reading.** The two are separated below because the evidence is not uniform across them: the novelty claim rests on the counted block, and the qualitative block is supporting context. Any headline sentence uses **11**, because that is the number a reviewer can re-run.

A blank cell means **the evidence base gives no count for that term in that instrument** — it is not a zero.

### 4a — Counted (11 instruments): the novelty claim rests here

| id | instrument | version / date | object protected | duration | how long | withstand | containment | egress | hours | minutes | time axis | count method | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I02 | SL5 Standard for AI Security | Preliminary draft v0.1, March 2026, arXiv… | physical perimeter: ICD-705 SCIF construction, Red Zone… | 0 | — | — | 2 | 4 | — | — | FALSE | full text term count | N6; evidence base 12 |
| I03 | GPAI Code of Practice, Safety & Security chapter | 2026 (143,901 characters counted) | model weights against self-exfiltration | 0 | — | — | 0 | 0 | — | — | FALSE | full text term count | N1; evidence base 12 |
| I04 | CSA AI Controls Matrix | v1.1.1, generated 2026-07-22, 247 control… | 247 controls across the AI stack | 0 | 0 | 0 | — | — | 0 | 0 | FALSE | full text term count | N2; evidence base 12, 12.1 |
| I06 | NIST SP 800-53 Rev. 5, SC-7 Boundary Protection | Rev. 5, 29 control enhancements | system boundary: deny-by-default, prevent exfiltration,… | 1 | 0 | 0 | — | — | 0 | 0 | FALSE | full text term count | N3; evidence base 12, 12.4 |
| I08 | Guidelight Control Standard | v1.1, published 2026-08-10 | six practices, all detection and reaction | 0 | — | 0 | — | — | — | — | FALSE | full text term count | N7; evidence base 12 |
| I09 | OpenAI Preparedness Framework | v2, December 2023, maintained | capability thresholds and safeguards | 0 | — | 0 | 0 | 0 | 0 | 0 | FALSE | partial read full term search | P15; evidence base 12 |
| I10 | GPT-6 Astra Safety Overview | 2026-09-03, 185,000 characters | customer-facing safety documentation for a Critical-can… | 0 | 0 | — | 0 | — | — | — | FALSE | partial read full term search | P16; evidence base 12 |
| I11 | Anthropic August Risk Report | August 2026, 186 pp., redacted | enterprise risk reporting | — | — | — | 1 | 1 | — | — | FALSE | term search only | P17; evidence base 12 |
| I12 | Moon and Varshney: Containment Verification - AI Safety Guarant… | arXiv 2605.09045, 14 pp., ICML 2026 works… | the agentic framework (containment layer) rather than t… | 0 | 0 | 0 | — | — | 0 | 0 | FALSE | full text term count aggregated over cluster | CV1; evidence base 11.7 |
| I13 | Hossain et al.: The Containment Gap - How Deployed Agentic AI F… | arXiv 2606.12797, 9 pp. | six containment principles from a compositional model o… | 0 | 0 | 0 | — | — | 0 | 0 | FALSE | full text term count aggregated over cluster | CV2; evidence base 11.7 |
| I14 | Metere: Methods for Formal Verification of Agent Skills - Three… | arXiv 2605.23951, 29 pp. | capability containment, mapped to EU AI Act Art. 9/13/1… | 0 | 0 | 0 | — | — | 0 | 0 | FALSE | full text term count aggregated over cluster | CV3; evidence base 11.7 |

Term counts for CV1–CV3 are given in the evidence base across the three cluster full texts **jointly**, not per paper. A zero total across three texts entails zero in each, so the zero counts are carried per row as deduction; `containment` and `egress`, which are non-zero and not splittable, are left blank.

The single `duration` in SC-7 (I06) is worth reading closely. It sits in SC-7.4 *External Telecommunications Services* — *“Document each exception to the traffic flow policy with a supporting mission or business need and duration of that need.”* That is the lifetime of an administrative exception to the policy, not the endurance of a boundary under attack. The one duration in the most comprehensive boundary-protection catalogue in existence measures paperwork.

---

### 4b — Qualitative (6 instruments): supporting context

No term count exists for these in the evidence base. Their gap is stated qualitatively, and they are reported separately so that no reader has to consult `count_method` to see which kind of evidence they are looking at.

| id | instrument | version / date | object protected | duration | how long | withstand | containment | egress | hours | minutes | time axis | count method | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I01 | RAND SL1-SL5 | RR-A2849-1, 2024 | model weights against theft; 38 attack vectors | — | — | — | — | — | — | — | FALSE | qualitative no term count | N5; evidence base 12 |
| I05 | NIST SP 800-53 Rev. 5, AU-9 and enhancements | Rev. 5 | records after they are created | — | — | — | — | — | — | — | FALSE | qualitative no term count | N3; evidence base 12 |
| I07 | Fujitsu: AI Sandboxes - A Threat Model, Taxonomy, and Measureme… | arXiv 2606.18532, June 2026, 50 pp. | 15 measurement dimensions for AI sandboxes | — | — | — | — | — | — | — | FALSE | qualitative no term count | N4; evidence base 12 |
| I15 | MITRE ATT&CK | 2026 | adversary tactics and techniques catalogue | — | — | — | — | — | — | — | FALSE | qualitative no term count | N10; X01 (assessment); evidence base 12, 6/K-5 |
| I16 | EU AI Act and NIST AI RMF, as mapped by CSA AICM | CSA AICM v1.1.1 mappings sheet, 2026-07-22 | general AI governance requirements | — | — | — | — | — | — | — | FALSE | qualitative no term count | N2 (mappings sheet); evidence base 12.2 |
| I17 | METR documented-incident catalogue (companion to the Frontier R… | 2026-05-19, updated since; 44 incidents | agent behaviour, scored for scope violation and conceal… | — | — | — | — | — | — | — | FALSE | qualitative no term count | N11; https://metr.org/agent-incidents/ |

**`time axis` is FALSE in all 17 rows.** `tests/test_registers.py::test_no_instrument_has_a_time_axis` fails if any instrument ever gains one, and a second test fails if the generated summary row in `data/instruments.csv` drifts from the rows it describes.

---

## Table 5 — The proposed control, in AICM column format

Parsed from [`docs/clause-ais-13-m.md`](../docs/clause-ais-13-m.md) §2, not transcribed, so this table cannot drift from the clause text. The clause extends an existing control rather than adding one: AIS-13 already requires an inventory and a completeness check — of *components* that execute, not of *mechanisms* by which a capability is realised.

| Field | Value |
|---|---|
| Control Domain | Application & Interface Security |
| Control Title | Capability Mechanism Inventory and Protection-Time Budget |
| Control ID | AIS-13.M |
| Control Type | AI-Specific |
| Cloud/AI Processing Infrastructure (PI) | Shared Cloud Service Provider–Model Provider (Shared CSP-MP) |
| Model | Owned by the Model Provider (MP) |
| Orchestrated Services | Shared Orchestrated Service Provider–Application Provider (Shared OSP-AP) |
| Application | Shared Application Provider–AI Customer (Shared AP-AIC) |
| Architectural relevance | Phys ✓ · Network ✓ · Compute ✓ · Storage ✓ · App ✓ · Data ✓ |
| Lifecycle relevance | Preparation: Resource provisioning · Development: Guardrails · **Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation** · Deployment: Orchestration · Delivery: Operations, Continuous monitoring |
| Threat categories | Model manipulation ✓ · Sensitive data disclosure ✓ · Insecure supply chain ✓ · Insecure apps/plugins ✓ · Loss of governance/compliance ✓ |

**Control Specification**

> Maintain, for each capability that a containment control is credited with blocking, an inventory of the mechanisms through which that capability can be realised; document the method by which the inventory was derived and justify its coverage; and where the control does not **eliminate** the capability, declare a protection-time budget for the control and re-verify it at an interval shorter than that budget.

Full text, including the implementation and auditing guidelines, the mapping and the scope limits, is in `docs/clause-ais-13-m.md`.

---

## Table 6 — Contradiction register

9 documented contradictions, **6 of them intra-document** — inside a single document. Detecting these is itself part of the result, not noise around it. Full claims for each row are in `data/contradictions.csv`.

### Main text

These four carry the argument and belong in the body of the paper.

| id | short title | intra-document | source A | source B | resolving question |
|---|---|---|---|---|---|
| W-1 | Origin date: 20 April against 8 May | yes | P1 III.A (and P4) | P1 section X | What happened on 20 April at 07:59 UTC, and why does the narrative in III.A begin on 8 May instead? |
| W-2 | State of knowledge on 27 June | yes | P1 III.B | P1 III.B (about ten lines later; P2 adds context) | If responders named the message board explicitly on 27 June, at which level was that information lost before 5 July? |
| W-8 | Rebuild date: P2 against everything else | no | P2 (event timeline) | P1 section X, P1 III.B, P4, P5 | Resolved: the blog post's event timeline is wrong. The rebuild was 2026-07-06 01:16 UTC. This is load-bearing - it is t0 for all three type-A rows, so every P_wall in this repository depends on it. |
| W-9 | The monitor calibrated on itself | yes | P2 | P2 (same blog post, 2026-08-26) | What recall did the monitor have on these behaviour types BEFORE the recalibration, and is that figure published? Without it, 'would have paged a day earlier' is unverifiable and does not transfer to… |

### Appendix

Documented, load-bearing for provenance, but not required by the argument.

| id | short title | intra-document | source A | source B | resolving question |
|---|---|---|---|---|---|
| W-3 | Harness attribution: ChatGPT against Codex | yes | P1 chapter VIII, introduction | P1 chapter VIII.D | One measurement with an inconsistent product name, or two measurements? A 100x reduction IS below one percent relative to baseline, so the orders of magnitude agree while the product does not. Withou… |
| W-4 | Transcript integrity: OpenAI against METR | no | P1 VIII.A | P5 (METR / Redwood) | Do 'the logs that our graders or monitors ultimately see' and 'transcripts' denote the same artefacts? |
| W-5 | May 26 activity: prose against the event table | yes | P1 III.A | P1 section X | At which level does 'unrelated' apply: workload, model, technique, or causal chain? |
| W-6 | Model designation: IM1 against HPIM | no | P1 / P2 | P5 (METR) | Are IM1 and HPIM the same model under two names, and what was redacted about its training and deployment? |
| W-7 | Start date of the ExploitGym runs | yes | P5, one passage | P5, another passage (and P1 III.B) | Did the ExploitGym runs start on 7 or 8 July? Minor, but it moves the start of the measured window. |

---
