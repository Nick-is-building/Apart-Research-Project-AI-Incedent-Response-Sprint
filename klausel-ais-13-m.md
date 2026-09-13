# AIS-13.M — Mechanism Inventory and Protection-Time Budget

**Proposed extension to CSA AI Controls Matrix v1.1.1, domain Application & Interface Security**

---

## 1. Design rationale

Existing containment controls are specified and audited as **properties of the control**: is isolation implemented, are resource limits set, are access controls in place. Every instrument surveyed states the requirement this way, and none attaches a duration to it.

The measured evidence from the one incident in which a containment control was defeated shows why this is insufficient. All three protection times were ended not by the control failing but by the blocked capability being realised through a **different mechanism** the control did not cover. The control was never overcome in any of the three cases.

This extension therefore shifts the audited object from the control to the **capability the control is credited with blocking**, and introduces the two quantities that follow from that shift: the inventory of mechanisms by which the capability can be realised, and the time for which the control is claimed to hold.

**Two deliberate design constraints:**

**It attaches to an existing control rather than creating a new one.** AIS-13 already requires an inventory and a completeness check — Auditing Guideline §2.1 and §2.2 — but of *components* that execute, not of *mechanisms* by which a capability is realised. The same procedure applied to the correct object. Adoption cost is therefore the cost of widening an existing audit step, not of adding a control.

**It does not require proving a negative.** The completeness of a mechanism inventory is not provable: no operator can demonstrate that no unlisted mechanism exists. The clause therefore makes the **claim** auditable rather than the fact, and closes the loop empirically — a measured protection time that ends via an unlisted mechanism is a recorded failure of the inventory, not only of the control.

---

## 2. Control row (AICM format)

| Field | Value |
|---|---|
| **Control Domain** | Application & Interface Security |
| **Control Title** | Capability Mechanism Inventory and Protection-Time Budget |
| **Control ID** | AIS-13.M |
| **Control Type** | AI-Specific |
| **Cloud/AI Processing Infrastructure (PI)** | Shared Cloud Service Provider–Model Provider (Shared CSP-MP) |
| **Model** | Owned by the Model Provider (MP) |
| **Orchestrated Services** | Shared Orchestrated Service Provider–Application Provider (Shared OSP-AP) |
| **Application** | Shared Application Provider–AI Customer (Shared AP-AIC) |
| **Architectural relevance** | Phys ✓ · Network ✓ · Compute ✓ · Storage ✓ · App ✓ · Data ✓ |
| **Lifecycle relevance** | Preparation: Resource provisioning · Development: Guardrails · **Evaluation/Validation: Evaluation, Validation/Red Teaming, Re-evaluation** · Deployment: Orchestration · Delivery: Operations, Continuous monitoring |
| **Threat categories** | Model manipulation ✓ · Sensitive data disclosure ✓ · Insecure supply chain ✓ · Insecure apps/plugins ✓ · Loss of governance/compliance ✓ |

### Control Specification

> Maintain, for each capability that a containment control is credited with blocking, an inventory of the mechanisms through which that capability can be realised; document the method by which the inventory was derived and justify its coverage; and where the control does not **eliminate** the capability, declare a protection-time budget for the control and re-verify it at an interval shorter than that budget.

**Elimination, defined.** A control eliminates a capability only where the interface or execution substrate required to produce the outcome is **structurally absent from the execution environment**, such that no software-level mechanism available to the workload can achieve it. Restricting, filtering or removing a particular means of invocation is not elimination; it removes one mechanism from the inventory.

**Scope limit on elimination claims.** Elimination is a claim about the execution environment, not about the model. A capability resident in model weights — including knowledge of how to reconstitute a removed state — cannot be eliminated by any control applied to the environment. Where the model was trained during a period in which the capability was exercised, an elimination claim must be limited to the environment and stated as such.

---

## 3. Implementation Guideline — Operator of the execution environment

> **Role note.** These guidelines address the party that operates the execution environment in which agents run, which is not always the Model Provider. In frontier-lab evaluation and internal deployment — the setting from which the supporting evidence is drawn — this is the Model Provider. In enterprise agentic deployments, where the model is consumed through an API and the sandbox, tools and network boundary are operated by someone else, it is typically the Application Provider. The AICM role columns in §2 are marked shared for this reason; §3 and §4 apply to whichever party holds the execution environment.

**3.1 Build a capability register.** For each containment control relied upon in evaluation or internal deployment, record the capability it is credited with blocking, expressed as an outcome rather than as a request type. "Prevent the worker from acting on attacker-chosen external content" is a capability. "Reject non-platform URLs" is a mechanism.

**3.2 Enumerate mechanisms per capability.** For each capability, list the mechanisms by which it could be realised. Cover at minimum: direct in-band paths; paths through supporting and shared services; paths through services the organisation does not operate; storage and cache substrates readable or writable by the workload; and paths that achieve the outcome without the request type the control inspects.

**3.3 Record the derivation method.** State how the list was produced — architecture review, interface enumeration, red-team exercise, incident history — and by whom. An inventory without a stated method cannot be assessed for coverage.

**3.4 Run and record a coverage attempt.** Task a red team, human or automated, with finding a mechanism not on the list. Record the budget, the duration, the access level granted, and the result. A null result with a stated budget is evidence; a null result without one is not.

**3.5 Declare a protection-time budget** for every control that does not eliminate the capability. The budget is the period for which the control is claimed to hold under adversarial pressure. It is a claim, not a measurement, and is to be recorded as such.

**3.5.1 Justify the budget against a stated basis.** Every declared budget must name its basis, drawn from: (a) measured protection times for comparable mechanisms, whether the operator's own or from the public record; (b) the endurance result of the coverage attempt in §3.4, in which case the budget may not exceed the demonstrated endurance; or (c) a stated conservative organisational default, recorded as such. A budget declared without a named basis is permitted but is recorded as unjustified, and is a finding under §4.5.

**3.5.2 The budget is an exposure, not a shield.** Because §3.7 records realisations of the capability against the declared budget, a longer budget increases rather than reduces the operator's exposure: a realisation at six hours against a declared six-month budget is a more serious finding than the same realisation against a declared forty-eight-hour budget. Under regimes where published framework commitments are assessable — California SB 53 §22757.15, and Code-of-Practice commitments under EU AI Act Article 101(1) — the declared budget is such a commitment. Inflating it to relax the re-verification interval under §3.6 is therefore self-defeating, and the clause relies on this rather than on a prescribed ceiling.

**3.6 Re-verify in two tiers.** Re-verification is staged, because a single interval cannot govern two activities of very different cost.

- **Automated verification** must occur at an interval **shorter than the declared budget**. This is the execution of synthetic integrity checks or canary runs against **every mechanism listed in the inventory**, confirming that each remains blocked. It is a regression suite, not an investigation, and is the activity the short interval governs. Where the organisation already operates under NIST SP 800-53 SC-7(10), this is the organisation-defined parameter for exfiltration-test frequency, and this control supplies the rule for setting it.
- **Adversarial coverage attempts** under §3.4 — the search for a mechanism *not* on the list — are triggered by event rather than by clock: on a material change to the execution environment, on a model version change crossing a declared capability threshold, and on any realisation recorded under §3.7.

Record each execution of both tiers. An operator that runs only the second tier at the short interval has misread this control; an operator that runs only the first has no coverage evidence.

**3.7 Record realisations via unlisted mechanisms.** Where the capability is realised through a mechanism absent from the inventory, record it against the inventory, not only against the control. This is the empirical test of §3.2 and the reason the clause does not require proof of completeness.

---

## 4. Auditing Guideline — Operator of the execution environment

Designed so that a third party can assess compliance **from documents alone**, without access to the operator's network, harness or live systems.

**4.1 Understanding the control environment.** Obtain the list of containment controls relied upon during evaluation and internal deployment, and the capability register from §3.1. Confirm each control maps to at least one declared capability and each capability is expressed as an outcome rather than as a request type.

**4.2 Obtaining and verifying the population.** Select a risk-based sample of capabilities. For each, obtain the mechanism inventory and cross-reference it against the operator's own documentation — interface and API specifications, service architecture diagrams, deployment manifests, network topology records, plugin and tool registries, and the list of third-party services the workload can reach. This is the procedure already specified in AIS-13 Auditing Guideline §2.2, applied to mechanisms rather than components.

**4.3 Testing coverage.** For each sampled capability, identify at least one mechanism present in the operator's own architecture documentation but absent from the inventory, or record that none was found. A mechanism absent from the inventory but visible in the operator's own documents is a finding without any need for system access.

**4.4 Assessing the derivation method and the coverage attempt.** Confirm §3.3 and §3.4 are documented. Assess whether the red-team budget was proportionate to the risk level of the capability. Record the budget as stated; do not accept a null result reported without one.

**4.5 Assessing the budget, its basis, and the cadence.**

For each non-eliminating control:

- Confirm a protection-time budget is declared, and that it names a **basis under §3.5.1**. Record the basis type. A budget without a named basis is recorded as unjustified and is a finding.
- Where the basis is the coverage attempt under §3.4, confirm the declared budget **does not exceed the demonstrated endurance**. A budget longer than the time the red team was given, or longer than the time it took to succeed, is not supported by the basis it names.
- Where the basis is measured protection times for comparable mechanisms, confirm the comparison is stated and the source identified.
- Confirm the **automated verification interval under §3.6 is shorter than the declared budget**, and that executions are evidenced against **every mechanism in the inventory**, not a subset.
- Confirm the **adversarial coverage attempts under §3.6 are triggered as specified** — on material change to the execution environment, on a model version change crossing a declared capability threshold, and on any realisation recorded under §3.7 — and that each trigger event since the last assessment has a corresponding record or a stated reason for its absence.
- Where the operator or the public record contains measured protection times for comparable mechanisms, compare them against the declared budget and record any order-of-magnitude divergence.

**4.6 Assessing recorded realisations.** Obtain the §3.7 records. Confirm each is recorded against the inventory. Repeated realisations via unlisted mechanisms for the same capability indicate the derivation method in §3.3 is inadequate, independent of the strength of any individual control.

---

## 5. Mapping

| Framework | Relationship |
|---|---|
| **CSA AICM AIS-13** | Extends. §2.1 and §2.2 already require an inventory and a completeness check, of components; this applies the same procedure to mechanisms. §4.1 already requires assessing whether the sandbox can "withstand adversarial attempts" — this supplies the missing measure. |
| **CSA AICM AIS-11** | Supplies the specification the control lacks. AIS-11 reads in full "Establish security boundaries for agents"; this defines what a boundary must be documented to have. |
| **NIST SP 800-53 SC-7(10)** | Supplies the fill rule for the organisation-defined parameter governing exfiltration-test frequency: shorter than the declared protection-time budget. |
| **NIST SP 800-53 SC-7** | Adds a duration dimension to boundary protection. The family's 29 enhancements contain no time concept; its single occurrence of "duration" refers to the lifetime of a policy exception. |
| **NIST SP 800-53 AU-9** | Complementary. AU-9 protects records after generation; this does not address record integrity. |
| **EU AI Act, GPAI Code of Practice** | Supplies an auditable object for Commitment 9 incident tracking. Code-of-Practice commitments are taken into account in fine assessment under Article 101(1). |
| **California SB 53 §22757.15** | A published protection-time budget is a framework commitment whose adherence is assessable. |

---

## 6. Cost

The only published first-party cost figure for a containment measure is OpenAI's estimate of **roughly 20% of the inference compute being monitored** for chain-of-thought monitoring, with a stated target of raising an alert within 30 minutes of concerning activity. That figure is scoped: it covers monitored inference compute, not total compute, and the monitoring was not applied to all tool-using workloads.

This control's cost profile is different in kind. It is a documentation and periodic-testing requirement rather than a continuous compute overhead, and it is applied **before** workloads start rather than during them. Its recurring cost is the re-verification interval; its one-time cost is the derivation of the inventory.

**Not quantified.** No operator has published the cost of maintaining a mechanism inventory, because none maintains one. Any figure given here would be invented. The honest claim is comparative, not absolute: the control does not require additional monitoring compute, and monitoring is the measure whose reliability the operators themselves report as declining.

---

## 7. What this control does not do

**It does not establish that an inventory is complete.** Completeness is not provable. It requires the claim, the method, a recorded coverage attempt, and a record of failures — not proof.

**It does not prevent circumvention.** It makes the circumvention route a recorded failure of a declared inventory rather than an unanticipated event.

**It does not replace monitoring.** It reduces the state space monitoring has to cover; it does not observe behaviour.

**It does not set a correct budget value.** No empirical basis exists for what a protection-time budget should be. Three measured values exist in the public record, all from one incident. The control requires the budget to be declared and re-verification to be faster than it; it does not say what the number should be.

**Its audit is document-based.** An operator that maintains inaccurate documentation will pass §4.2 and §4.3. This is a limitation it shares with every framework that audits without system access, and it is the reason §3.7 exists — the empirical record is the check the documents cannot provide.
