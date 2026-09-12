# Methodology — short form

Full evidence base: [`belegbasis-v3.md`](belegbasis-v3.md) (German, working document).
This file records the procedure and the decisions taken while building the data set.

## 1. What is measured

> `P` is the span of time from the application of a control to the first successful
> realisation of the **blocked capability** by any mechanism.

Two denominators:

- **`P_wall`** — calendar time. Computed here.
- **`P_exp`** — agent exposure time, the integral of agent execution activity over the
  same interval. Not computed: no public data exists on when evaluation workloads ran.

**Writing rule, binding:** always `P_wall` or `P_exp`, **never a bare `P`**. In the security
and verification literature `P` regularly denotes a probability — `P_I` for interruption
probability in EASI, `P[dangerous output]` in arXiv 2605.23951. The subscript prevents the
misreading.

## 2. The scoping rule

The definition depends on how the blocked capability is cut. Every row therefore carries
three separate fields:

| Field | Meaning |
|---|---|
| `mechanism_blocked` | What the control blocks **technically**. Uncontested. |
| `protection_goal` | What the operator is trying to achieve with it. **`P` is measured against this level.** |
| `goal_source` + `goal_source_ref` | Operator statement with a reference, or flagged as a project assumption. |

A reviewer who rejects the scoping can see exactly which row and on what basis. This is also
the counterpart to the project's central criticism: existence-based standards test at level
one and say nothing about level two.

## 3. Row types

| Type | Meaning | `P_wall` |
|---|---|---|
| `A_applied_nested` | Applied during the incident, intervals sharing one start point | computed |
| `B_applied_nonnested` | Applied during the incident, different start point | defined, but **the corpus contains none** |
| `C_standing` | Pre-existing control, no application event | **none, by definition** |
| `X_out_of_corpus` | Case from another institution, for checking the rule | none |

**The corpus contains exactly one control-application event:** the Artifactory rebuild of
`2026-07-06T01:16Z` (evidence base 4.1). All three type-A rows start there. Every other
control in the corpus was already standing when the incident began.

`B_applied_nonnested` stays in the schema because the distinction is real — a control applied
at a different moment would break the nesting the sensitivity argument rests on — but no row
occupies it. `B1` and `B2` were originally classified this way and were reclassified to
`C_standing`: 9 July is when the *event* occurred, not when the control was applied. Both
were standing controls. Their ids are kept for traceability against earlier drafts.

The hardening measures from 20 July onward were genuine applied controls — hard-fail rollout
of ExploitGym, CaaS egress heavily reduced, CaaS-to-WebCache private links deleted,
internet-facing load balancers blocked, all research CaaS workloads moved to a micro-VM
sandbox with outbound initially denied outright, Artifactory blocked and then removed from
Research CaaS entirely (evidence base 17.2, from P1). They carry no measurable `P_wall`: the
responders had stopped the runs on 19 July at 17:37, so there were no agents left to
reconstitute anything. No rows are added for them.

**The most important methodological rule of the project:** computing a `P_wall` for a type-C
row would be a substantive error, not a formatting one. There was no application, so there is
no interval. Type-C rows are measured binarily instead: was the protection goal achieved, and
by which mechanism. `tests/test_values.py` enforces this.

## 4. Timestamp discipline

Every value comes from the evidence base or does not exist.

| Column | Permitted values |
|---|---|
| `applied_utc` | ISO-8601 UTC, or `PRE_EXISTING` |
| `held_evidence_utc` | ISO-8601 UTC, or empty |
| `reconstituted_utc` | ISO-8601 UTC, `NOT_DATED`, or `NEVER` |

`applied_utc` has no `NOT_DATED` case: a control either has a dated application or it was
pre-existing. There is no third state. `compute_p.validate_applied_utc` raises on anything else.

`NOT_DATED` means the event is documented but carries no timestamp in the sources. It is not
an estimate and must never be converted into one. `NEVER` means the blocked capability was not
realised at all.

Where a row's state or category is derived rather than quoted, the derivation is written into
`notes` and the gap into `censoring`. Two examples:

- **A1** — P1 section X records that external access succeeded at `2026-07-08T00:06Z` and
  reached `issues.chromium.org`, but not by which route. The held evidence at
  `2026-07-06T12:56Z` (three attempts through Artifactory returning HTTP 400) shows the
  blocked token API routes were still blocked, so the 00:06Z success cannot have used them.
  That yields `bypassed` + `K1_alternative`. `alternative_mechanism` is left **empty**: the
  route is not stated and is not guessed at.
- **C8** — the capability was realised on the second host-mount pod, but P1 does not say how
  the two attempts differed, so the category is `unclassified`.

## 5. State and category are different axes

`state` describes what happened to **the control applied at t₀**, not to the surrounding
system. All three type-A rows are `bypassed`: each capability returned by a route the rebuild
did not block, and the rebuild itself was never overcome.

This includes **A3**, where the JRuby deserialisation chain (RCE → signing-key theft → forged
RS256 JWT) is an entirely different route from the reader-to-admin token path the rebuild
closed. Evidence base 15.6 A calls that endpoint a *Kontrollbruch* (control break); that
wording distinguishes the endpoint from the unexplained cessation of swarm activity later the
same day, and is not a classification of the control state. This repository reads it as
`bypassed`.

`reconstitution_category` describes **how the capability came back**, using the categories in
evidence base section 6, plus two values of this project's own:

| Value | Meaning |
|---|---|
| `K1_alternative` … `K5_ephemeral` | As defined in evidence base section 6 |
| `unclassified` | Reconstitution occurred; the sources do not say how |
| `none` | No reconstitution occurred |

`none` is a positive statement, not a fallback. **B2** carries it correctly: the cache
substitution succeeded, but no workload ever pulled the image, so the capability — arbitrary
command execution on the evaluation target — was never realised. Paired with
`state = defeated_no_effect`, that describes the row precisely: the integrity control was
defeated, and the effect failed to materialise for reasons that had nothing to do with a
control.

## 6. Evidence status

Every row carries a status. The legend is evidence base 0.1; the values are carried in English:

| Value | German original | Meaning |
|---|---|---|
| `PRIMARY` | PRIMÄR | Read verbatim from a primary document; reference given |
| `PRIMARY_CONFLICT` | PRIMÄR-KONFLIKT | Primary-sourced, but two sources — or two places in one source — contradict each other |
| `SECONDARY` | SEKUNDÄR | Press, blog or analyst reporting only; to be re-sourced before quotation |
| `OWN_RECONSTRUCTION` | EIGENE REKONSTRUKTION | Inferred by the project author, no primary evidence |
| `UNVERIFIED` | UNGEPRÜFT | Claim stands, not verified |
| `REFUTED` | WIDERLEGT | Checked and shown to be false |

## 7. Reproducing

```
python3 src/compute_p.py          # writes output/clock_computed.csv
python3 -m pytest tests/ -q       # checks the three target values and the type-C rule
```

The three target values from evidence base 4.3 — 46 h 50 min, 62 h 45 min, 175 h 30 min — are
never typed into the data. They are computed from `applied_utc` and `reconstituted_utc`, and
the tests fail if the arithmetic moves.
