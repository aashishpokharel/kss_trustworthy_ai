# KSS — Trustworthy AI: Slide Build Architecture & Agent Instructions

**Audience for this document:** the AI coding agent responsible for producing the actual `.pptx` file.
**Not** a slide outline — this is the *specification* the agent must follow while it builds, edits, and QA's the deck.

---

## 0. Mission Brief

You are extending `KSS_template.pptx` (Fusemachines AI School branding) into a complete "KSS — Trustworthy AI" deck. The template, prior KSS slide decks, their build scripts, and the overall project architecture already exist in your workspace (`docs/` and the project root) (previous slides and other resources lie in `presentations/`) — read them before writing anything. Your job is to:

1. Reuse the existing template's master/layouts — never invent a new visual system.
2. Fill in every placeholder (`<Text Here>`, `<Notes>`, `<Something related to question (in red)>`, `<The answer>`, empty numbered rows) with real, reviewed content.
3. Do this while treating the **Presentation Principles in Section 1 as hard constraints**, not style suggestions. A slide that violates a "Never" rule below is a build failure, not a taste difference — fix it before moving on, the same way you would fix a validator error.

If any instruction in a source content doc conflicts with Section 1, Section 1 wins. Flag the conflict in your summary instead of silently picking one.

---

## 1. The Rulebook (non-negotiable)

Organized into the same four pillars the user specified, each rule expanded with the *why* and a concrete pass/fail test the agent can self-check against.

### 1.1 Structure & Simplicity

| Rule | Test |
|---|---|
| **One idea per slide.** If a topic needs two claims, it needs two slides — build progressively rather than stacking. | Can you summarize the slide's takeaway in one sentence? If it takes "and," split it. |
| **Headline messaging.** Titles are claims, not labels. `"GPUs cut training time by 6x"`, not `"GPU Performance"`. | Does the title alone convey the conclusion without reading the body? |
| **Eliminate slide-uments.** Slides support spoken narration; they are not the leave-behind report. Minimal bullets, no paragraphs. | Would this slide still make sense as a report page with no presenter? If yes, it's a document, not a slide — cut it down. |
| **6×6 guideline.** Cap at ~6 bullets, ~6 words per line, as an upper bound not a target — fewer is better. | Count words per line and bullets per slide before finalizing. |
| **No orphaned template placeholders.** Every `<...>` bracket, numbered box (`1`, `2`, `3`), and "Notes" field in the template must be either filled with real content or its container removed entirely (not left blank). | `markitdown` grep for `\[insert|TODO|lorem|<.*>|^\d$` must return nothing in the final deck. |

### 1.2 Visual Design & Hierarchy

| Rule | Test |
|---|---|
| **Visual hierarchy.** Title > key data point > supporting text, expressed through size/weight, not just position. | Squint at the slide — does your eye land on the title first, then the single most important number/claim? |
| **High contrast.** Body copy must be legible against its background at a glance. | No light-gray-on-cream, no dark text on the template's dark blue title-slide background. |
| **Embrace white space.** Do not fill the canvas because space is available. | Is there breathing room (≥0.5" from slide edges, ≥0.3" between elements)? If every inch is used, remove something. |
| **Never fake structure with decoration.** No added accent stripes, sidebar bars, or under-title lines beyond what the template itself already defines (the template's existing blue corner triangle and blue title-tab are fine — do not add more). | Compare each new slide's decoration against slide 2 ("Overview") of the template — any extra bar/stripe you introduced is a defect. |

### 1.3 Layout & Alignment

| Rule | Test |
|---|---|
| **Proximity & alignment.** Group related items; align to a shared grid (use the template's existing left margin and numbered-box column as the grid). | Do all numbered boxes, icons, and body text blocks share the same left edge as the template original? |
| **Rule of thirds.** Place the single most important visual/data point on a third-line intersection, not dead center by default. | For image-and-text slides (like "ML Infrastructures"), does the diagram sit in the right two-thirds while text anchors the left third — matching the template's existing pattern? |
| **Consistent spacing system.** Pick one spacing unit (the template uses ~0.3"–0.5" gaps between numbered rows) and reuse it everywhere. | Are gaps between repeated elements (numbered items, bullet rows) identical across all slides, not eyeballed per-slide? |

### 1.4 Cohesion

| Rule | Test |
|---|---|
| **Repetition.** Same fonts, same blue/gray palette, same header treatment (bold dark-gray title + blue left tab) on every slide. | Pull two slides side by side — could a viewer tell they're from different decks? They shouldn't be able to. |
| **Purposeful imagery only.** Diagrams/photos must clarify or add evidence — no generic clip art, no decorative filler. | For every image on a slide, can you state in one sentence what claim it supports? If not, remove it. |
| **Minimal to no animation/transition.** | Do not add slide transitions or build animations unless explicitly requested. |
| **Footer/branding consistency.** The "Fusemachines AI School" footer lockup must appear in the same position/size on every content slide, matching the template. | Compare footer x/y coordinates across slides — must be identical. |

### 1.5 Additional principles (research-sourced, supplementing the above)

Pulled from current presentation-design guidance (SlideSpeak, Noun Project, Microsoft PowerPoint design guidance, Smallppt UX principles, Pitchworx) to close gaps the user's list didn't fully cover:

- **Typography discipline:** maximum 2 font families in the whole deck; sans-serif for on-screen legibility; body text large enough to read from the back of a room (≥18pt body, ≥28–36pt titles). Match whatever the template's theme fonts already define — don't introduce a third font.
- **Storytelling arc:** structure the deck as problem → evidence/mechanism → resolution, not a flat list of topics. The existing "Overview" slides (Topic 1/2, then a continuation with 3 numbered items) should map cleanly onto this arc — use the numbering to signal narrative sequence, not just a table of contents.
- **Data visualization fit-for-purpose:** if you add charts/comparison tables (e.g., the referenced CPU-vs-GPU comparison table), pick the chart type for the claim — proportions → simple bar, not pie with many slices; trends → line; direct spec comparison → table with the differentiating row visually emphasized (bold or colored cell), not a wall of uniform text.
- **First-slide credibility:** title slide (already built) sets tone — do not alter its template styling; only confirm the title text is the final, approved title.
- **Consistency over cleverness:** if a design choice (icon style, number-badge treatment) exists in the template, propagate it rather than inventing a new treatment for later slides, even if you think it's an improvement — deck-wide consistency outranks any single slide looking "nicer."

---

## 2. Step-by-Step Agent Workflow

Follow this sequence. Do not skip steps or reorder structural work after content work (see step 3 — this mirrors the pptx skill's own ordering requirement).

### Step 1 — Reconnaissance (read before writing)
1. Read the existing KSS build docs/architecture in `docs/` and project root, and any prior KSS slide scripts already in the workspace, so new slides match established conventions (naming, layout choices, tone).
2. Run the template thumbnail grid to see every available layout at a glance:
   ```
   python scripts/thumbnail.py KSS_template.pptx kss-template-thumbs
   ```
3. Dump current text content to find every unresolved placeholder:
   ```
   markitdown KSS_template.pptx
   ```
   Note every `<...>`, empty numbered box, and "Notes" field — this is your placeholder backlog.

### Step 2 — Content Planning (before touching XML)
For **each** slide, write down before building:
- The one-sentence takeaway (this becomes the headline).
- Which template layout it reuses (title / section-overview / content-with-image / comparison).
- What single visual (if any) supports the claim, and why.

Reject any planned slide that fails the "one idea" or "purposeful imagery" tests in Section 1 before it's built — cheaper to fix in planning than in XML.

### Step 3 — Structural Work First
All slide duplication, insertion, reordering, or deletion happens **before** any content editing:
```
python3 -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall('unpacked')" KSS_template.pptx
python scripts/add_slide.py unpacked/ slideN.xml --after slideM.xml   # duplicate the right layout per planned slide
# reorder/delete via <p:sldIdLst> in ppt/presentation.xml
python scripts/clean.py unpacked/     # only after slide list is final
```
Reason: duplicating after editing clones your edits onto every copy; clean.py deletes anything not yet registered in the slide list.

### Step 4 — Content Fill
- Edit `ppt/slides/slideN.xml` directly, one `<a:p>` per bullet/list item — never concatenate items into one paragraph.
- Preserve existing formatting: copy sibling `<a:pPr>` properties rather than writing fresh ones; bold titles/labels via `<a:rPr b="1">`.
- Replace every placeholder identified in Step 1. If a template slot has more numbered rows than you have content for (e.g., template has boxes `1/2/3` but you only need two points), delete the unused box's full group (badge + text), not just its text.
- Populate speaker notes (the template's `<Notes>` field) via the proper notes part — not as an on-slide text box.
- For the CPU/GPU comparison table referenced in the source material: build it as a real table (or native chart) inside the slide, with the deciding factor (e.g., parallelism/throughput) visually emphasized — not as another bullet list.

### Step 5 — Repack & Validate
```
(cd unpacked && rm -f ../KSS_output.pptx && zip -Xr ../KSS_output.pptx .)
python scripts/office/validate.py KSS_output.pptx --original KSS_template.pptx
```
Fix every reported error in the generator/XML edit itself, not by hand-patching the zip. Re-run until clean.

### Step 6 — Content QA
```
markitdown KSS_output.pptx | grep -iE "\bx{3,}\b|lorem|ipsum|\bTODO|\[insert|<.*>|this.*(page|slide).*layout"
```
Zero results required. Also re-read every headline against the "headline messaging" test — generic labels ("Results", "Overview", "Topic 1") must have been replaced with claims, except where "Overview" itself is the deliberate section-divider label used by the template's own design (that one stays, since it's a navigation slide, not a content slide).

### Step 7 — Visual QA (mandatory, do not skip)
```
python scripts/office/soffice.py --headless --convert-to pdf KSS_output.pptx
pdftoppm -jpeg -r 150 KSS_output.pdf slide
```
View every rendered slide fresh (not from memory of the generating code) and check, per slide, against the **full checklist in Section 3** below.

### Step 8 — Principle Audit (final gate)
Before declaring done, re-walk Section 1 rule-by-rule against the rendered images — this is the step most likely to be skipped under time pressure and the one the user most explicitly required. Produce a short pass/fail note per pillar (Structure, Visual Design, Layout, Cohesion) in your final summary to the user.

---

## 3. Visual QA Checklist (per rendered slide)

- [ ] No text overflow or clipping at any box/slide edge
- [ ] No overlapping elements (text through images, lines through words)
- [ ] Footer/branding lockup identical position across slides
- [ ] Gaps between elements ≥0.3", margins from slide edge ≥0.5"
- [ ] No uneven whitespace (dense in one corner, empty in another)
- [ ] Column/box alignment consistent with the template's existing grid
- [ ] Contrast sufficient (no light-on-light, dark-on-dark)
- [ ] No added accent stripes/bars beyond the template's own design
- [ ] No leftover placeholder text or empty numbered badges
- [ ] Every image on the slide supports a stated claim
- [ ] Title is a headline/claim, not a generic label (where applicable)
- [ ] Font families match the template theme (no third font introduced)

---

## 4. File & Naming Conventions

- Work inside the existing project structure; do not create a parallel folder hierarchy.
- Output file: `KSS_output.pptx` during iteration; final deliverable renamed to match the organization's existing KSS naming convention (check prior decks in the workspace for the pattern before finalizing).
- Keep the `.pptx` template's theme/master files untouched — all new slides must reference the existing layouts, not new ones, unless a genuinely new content type (e.g., the comparison table) requires duplicating and lightly adapting the closest existing layout.

---

## 5. Definition of Done

A slide/deck is complete only when **all** of the following are simultaneously true:
1. `validate.py --original` passes clean.
2. Placeholder grep in Step 6 returns nothing.
3. Visual QA checklist (Section 3) passes on every slide.
4. Section 1 rulebook self-audit (Step 8) is passed and documented, pillar by pillar.

If any of the four fail, the deck is not ready — iterate on the specific failing slide, re-run only that slide's QA, and re-confirm before reporting completion to the user.
