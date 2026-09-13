# Submission template and requirements

Apart Research AI Incident Response Sprint. Deadline **Sunday 14 September 2026, 23:59 AoE**
(= Monday 15 September, 13:59 CEST).

---

## Template structure — NOT RETRIEVED

**The official template could not be fetched from this environment, and nothing below
reconstructs it.**

The current sprint page does not link the template. The previous sprint's link is:

```
https://docs.google.com/document/d/13GhHIya82BXAnJ5G-iiac6fgDEMxJdu2DdUK7A_jQyc/copy?usp=sharing
```

Two retrieval attempts, both refused before reaching Google:

| Attempt | Result |
|---|---|
| Automated page fetch of the `/copy` URL | `EGRESS_BLOCKED — access to docs.google.com is blocked by the network egress proxy` |
| `curl` of `/export?format=txt` and of `/edit` | `curl: (56) CONNECT tunnel failed, response 403` |

This is the sandbox's egress policy refusing the host, not a permissions or sharing problem on
the document. A person opening the link in a browser will very likely get it without trouble.

**Section order, headings, formatting conventions and length expectations are therefore
unknown.** Writing a plausible-looking template here would be indistinguishable from the real
one to anyone reading this file later, and would be wrong in ways nobody could detect. It is
left blank on purpose.

**To fill this in:** open the link, then record — verbatim — every section heading in order, any
per-section word or page limits, heading levels, citation style, and any instructional text the
template carries. Replace this section; leave the requirements below untouched.

---

## Submission requirements

From the previous sprint, verbatim.

**Required**

- Research report (PDF) using the official template
- Project title and abstract, 150 words or fewer
- Author names and affiliations
- Limitations and Dual-Use / Ethical appendix
- links work

**Optional**

- Public GitHub repo
- a 3 to 5 minute video demo

**Framing**

> "Think of it as a mini research paper documenting your problem, approach, results, and
> implications, not a product demo."

---

## What this repository already supplies against those requirements

Mapping only — none of this is paper content.

| Requirement | Where it comes from |
|---|---|
| Limitations appendix | [`docs/limitations.md`](limitations.md) — seven limitations, written for a hostile reviewer, plus what would change the result |
| Dual-use / ethical appendix | [`README.md`](../README.md), "Dual use" section — no exploit code; the mechanism inventory is the riskier artefact and belongs in auditor disclosure, not in public |
| Results tables | [`output/paper_tables.md`](../output/paper_tables.md) — five tables, generated from the data |
| Figures | `output/figure_1..4 .png` and `.pdf`, 300 dpi and vector |
| Links work | Every source cited by a short code registered in `data/sources.csv` with a full URL; a test fails if a file cites an unregistered code |
| Public GitHub repo (optional) | This repository; `./verify.sh` reproduces every number in one command |

Two things a reader should be told explicitly in the paper, because they are easy to get wrong
from the tables alone: the corpus contains **exactly one control-application event**, so there
are three measured protection times and not twenty-two; and the three out-of-corpus rows are
checks on the rule, **not** additional measurements.
