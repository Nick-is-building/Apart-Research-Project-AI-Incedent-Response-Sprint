# Submission template and requirements

Apart Research AI Incident Response Sprint. Deadline **Sunday 14 September 2026, 23:59 AoE**
(= Monday 15 September, 13:59 CEST).

---

## Template structure — PENDING

**Not recorded. The official template has not been read, and nothing here describes it.**

It could not be fetched from this environment: `docs.google.com` is refused by the network
egress proxy before any request reaches Google (automated fetch: `EGRESS_BLOCKED`; `curl`:
`CONNECT tunnel failed, response 403`). The template is to be uploaded to the repository
instead.

**When it is in the repository:** read it and replace this section with its actual structure —
every section heading in order, heading levels, any per-section word or page limits, citation
style, and any instructional text it carries. Leave the requirements below untouched.

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

## Status against those requirements

| Requirement | Status |
|---|---|
| Research report (PDF) using the official template | Text assembled at `output/paper.md`; **template not applied** — pending the template |
| Title and abstract, 150 words or fewer | 149 words, unedited |
| Author names and affiliations | In the assembled paper |
| Limitations and Dual-Use / Ethical appendix | Appendix C (from `docs/limitations.md`) and Appendix D |
| Links work | Every source cited by a code registered in `data/sources.csv`; a test fails if a file cites an unregistered code |
| Public GitHub repo (optional) | This repository; `./verify.sh` reproduces every number in one command |
| Video demo (optional) | Not produced |
