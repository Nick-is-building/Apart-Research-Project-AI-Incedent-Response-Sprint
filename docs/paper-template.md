# Submission template and requirements

Apart Research AI Incident Response Sprint. Deadline **Sunday 14 September 2026, 23:59 AoE**
(= Monday 15 September, 13:59 CEST).

Template file in the repository: `Digital Minds Research Sprint submission template.docx`.
Note the filename: it is the Digital Minds sprint's template, which is the one supplied.

---

## Template structure, as read from the file

### Page setup

| Property | Value |
|---|---|
| Page size | US Letter, 12240 × 15840 DXA (8.5 × 11 in), portrait |
| Margins | 1 in on all four sides; header and footer 0.5 in |
| Default font | Arial 11 pt (`w:sz` 22 half-points) |
| Line spacing | 276/240 = 1.15, applied as the document default |
| Named styles available | Title, Subtitle, Heading1–Heading6, Normal, Table1–Table5 |
| List numbering | `numId` 1 decimal `%1.`, 2 lower-letter `(%1)`, 3 bullet `-` |

### Stated length expectation

> **Recommended length: 4 pages excluding references and appendix.**
> Rough guide: Intro & Related Work 1p, Methods and Results: 2.5p, Discussion 0.5p.

### Section order, verbatim from the template

1. A title block table: **PROJECT TITLE** (Title style), then author names and affiliations,
   then "With Apart Research", then **Abstract**.
2. An instructional info box table — *"Delete all guidance text including this info box before
   submitting."*
3. `1. Introduction` (Heading2)
4. `2. Related Work` (Heading2)
5. `3. Methods` (Heading2)
6. `4. Results` (Heading2)
7. `5. Discussion and Limitations` (Heading2), with `Limitations` and `Future Work` as
   Heading3 subsections
8. `6. Conclusion` (Heading2)
9. `Code and Data` (Heading2)
10. `Author Contributions (optional)` (Heading2)
11. `References` (Heading2)
12. `Appendix (optional)` (Heading2)
13. `LLM Usage Statement` (Heading2)

### Formatting conventions the template states

- Abstract: **150–250 words**.
- Number all figures (Figure 1, Figure 2…) and tables (Table 1, Table 2…).
- Captions must be understandable without the main text.
- Place figures and tables near where they are first referenced.
- Ensure text in figures is legible.
- References: consistent citation format, with author, year, title, venue and URL or DOI.
- Replace the italicised guidance text under each heading; delete all guidance before
  submitting.
- *"The section structure is strong guidance but not rigid. If your project requires a
  different organization, feel free to adapt."*

---

## How the paper was placed into it

`src/build_submission.py` rebuilds `word/document.xml` from `output/paper.md` and leaves
`styles.xml`, `numbering.xml`, the theme, the embedded fonts and the section properties exactly
as the template defines them, so the output carries the template's typography rather than an
imitation of it. The guidance info box is dropped, as the template instructs.

Two adaptations, both permitted by the template's own "strong guidance but not rigid" note:

- **Future Work stays a top-level section.** The template nests it under `5. Discussion and
  Limitations`; the paper keeps it as section 7, after the conclusion. Moving it would have
  reordered authored prose.
- **Limitations appear twice by design.** A short paragraph closes section 5, as the template
  expects, and the extended version is Appendix C.

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

**One conflict between the two.** The requirement list says *150 words or fewer*; this template
says *150–250 words*. The abstract is **149 words** and was not edited. It satisfies the
requirement list and falls one word below the template's stated minimum.

---

## Status against those requirements

| Requirement | Status |
|---|---|
| Research report using the official template | `output/paper.docx`, built from the template; schema-validated against it |
| PDF | **Not produced here.** LibreOffice fails on every input in this environment, including a plain `.txt` and the untouched template itself, so it is the sandbox and not the document. Convert on a normal machine. |
| Title and abstract | 149 words, unedited — see the conflict noted above |
| Author names and affiliations | In the title block |
| Limitations and Dual-Use / Ethical appendix | Appendix C and Appendix D |
| Links work | Every source cited by a code registered in `data/sources.csv`; a test fails if a file cites an unregistered code |
| Public GitHub repo (optional) | This repository; `./verify.sh` reproduces every number in one command |
| Video demo (optional) | Not produced |
