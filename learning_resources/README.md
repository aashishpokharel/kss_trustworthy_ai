# 📚 Learning Resources

Student-facing companion material for the KSS × Fusemachines Fellowship module
**"Responsible and Trustworthy AI"** (Explainable AI, Causal AI, and the
surrounding principles of fairness, robustness, privacy and accountability).

| File | What it is |
|------|------------|
| `Responsible_and_Trustworthy_AI_Learning_Resources.md` | **Source of truth.** Full learning-resources document, structured as **Heading → Learning Objectives → Contents to cover → Resources + Additional Materials**. |
| `Responsible_and_Trustworthy_AI_Learning_Resources.pdf` | Rendered, printable version of the Markdown. |
| `build_pdf.py` | Generator that turns the Markdown into the PDF. |

## Regenerating the PDF

The generator depends only on [`reportlab`](https://pypi.org/project/reportlab/)
(a build-time tool — the teaching code itself has **zero** runtime
dependencies) and uses the built-in Helvetica / Courier fonts, so no system
fonts are required.

```bash
pip install reportlab
python3 learning_resources/build_pdf.py
```

The script reads `Responsible_and_Trustworthy_AI_Learning_Resources.md` and
writes `Responsible_and_Trustworthy_AI_Learning_Resources.pdf` next to it.
Re-run it whenever you edit the Markdown.

## Notes

- The Markdown is the single source of truth — always edit the `.md`, then
  rebuild the PDF. Never hand-edit the PDF.
- Because the base PDF fonts use the WinAnsi (cp1252) encoding, `build_pdf.py`
  transliterates two glyph families that are not otherwise representable: the
  right arrow becomes `->`, and the box-drawing characters in the repository map
  become ASCII (`|--`, `` `-- ``, `|`). Everything else (em/en dashes, `×`, `·`,
  the bullet `•`) is preserved.
- The content is grounded in the runnable code in this repository — see
  `trust_safety/`, the numbered teaching folders, `questions/` and
  `5_responsible_trustworthy_ai/`.
