# Blog style guide

The style this blog should follow — the **core style**, the **visual design**, and the **writing voice**.

Reference writers:
- [Sebastian Raschka, *LLMs-from-scratch*](https://github.com/rasbt/LLMs-from-scratch) — build the thing in minimal, runnable code, and explain every line.
- [Horace He, *Making Deep Learning Go Brrr From First Principles*](https://horace.io/brrr_intro.html) — explain performance and systems work from the hardware up, with the arithmetic in the open.
- [Lilian Weng](https://lilianweng.github.io/posts/2025-05-01-thinking/) — structure and rigor; citation-heavy surveys.
- [nrehiew / wh](https://nrehiew.github.io/blog/sft_rl_opd/) — intuition-first, opinionated, a unifying lens.

---

## Core style — public technical writing with code

Every post is **technical writing an engineer can learn from**: it explains a mechanism, or a
performance/systems phenomenon, clearly enough that the reader could build or measure it
themselves. Code and numbers are first-class components, not decoration. This is usually
*paired* with a survey or an argument (the Weng/nrehiew half) rather than standalone.

**Code — the Raschka half**
- Build the mechanism **from scratch** in **minimal, runnable PyTorch**: the smallest module that
  exhibits the idea (a forward pass, a training step, an exit rule), not a library wrapper.
- **One idea per block, ≤ ~30 lines.** If it needs more, it is two ideas.
- **Every line is explained** — by a comment when it is a constraint the code can't show, by
  prose right before or after the block for the *why*. Name the real paper the trick comes from.
- Use the paper's own names and defaults (`r_bar = 32`, `k = 8`) so the reader can map code to source.
- **Run it before publishing.** Every block in a post has been executed; if it prints, the printed
  output is what the post shows. Snippets that are pseudocode say so.

**Performance — the Horace He half**
- Explain with the three regimes: **compute-bound, memory-bandwidth-bound, overhead-bound.**
  Say which one applies, and show the arithmetic: bytes moved, FLOPs, the ratio, the roofline.
- **Real hardware numbers** (H100: ~3.35 TB/s HBM, ~990 TFLOP/s dense bf16), real model
  numbers (parameters, layers, cache bytes per token), a real batch size — then the estimate.
- Back-of-envelope calculations are shown in the open, as a short code block that prints them,
  and labelled as a **model** until a measurement is cited. Never let an estimate read as a
  benchmark.
- Prefer the counter-intuitive consequence stated plainly ("below the saturation batch, an early
  exit saves FLOPs but not wall-clock").

**Where code goes in a post**
- Right after the figure or table it explains, never in a separate appendix.
- **Collapsed by default.** Each block sits in `<details class="code">` with a `<summary>` that says what
  it is and how long it is ("Code — a looped language model in 30 lines"); its printed output folds with
  it. The prose must read complete without opening anything — quote the numbers the block prints.
- A post has as much code as it needs to make the mechanism concrete — typically 3–6 short
  blocks — and no more. It stays figure-led (see below).

## Figure-led, not prose-led

- Each section is carried by a **figure or a table**, with one or two short paragraphs at most.
- **Enumerable facts go in tables** (verdicts, ingredients, failure modes, claim vs measurement).
- **Interactive figures** where the reader can *turn the dial* the section is about (sliders,
  toggles). Static SVG otherwise. One claim per figure.
- Draft short first; do not write a survey and cut it down.

## Scope: this guide is for the blog, not the reports

Tech reports (`reports/`) share the repo but are deliberately a **different design** —
grey paper, Source Serif 4 / Inter / Geist Mono, a sticky sidebar, self-contained pages
with inline CSS. Do not restyle them to match the blog, and do not list or link them on
the Writing page; they are reached from the **Reports** tab. Their conventions live in
`reports/README.md`.

---

## Visual design (modeled on Hugo PaperMod, like Lilian Weng's site)

| Element | Spec |
|---|---|
| **Content column** | 720px text (`max-width: 768px` incl. 24px gutters), centered |
| **Body font** | system sans stack (`-apple-system, …`), **16px**, **line-height 1.6** |
| **Theme** | fixed light/white (`color-scheme: light`); no dark mode |
| **Palette** | bg `#fff` · text `#1b1b1a` · muted `#6b6b66` · accent `#b5482e` · borders `#ececec` |
| **Body links** | dark text, underlined; hover → accent |
| **Headings** | h1 large bold; h2 ~24px; h3 ~18–19px; tight line-height (~1.2) |
| **TOC** | bordered light-grey (`#f6f6f4`) collapsible box at top of post; compact, muted-grey links, 14px |
| **Figures** | full column width for data figures; **no border**, centered grey caption (13px). Lead caption with bold `Figure N — Title.` |
| **Tables** | full width, 14–15px, thin rules only, bold first column for label-like cells; wrap wide tables in a horizontally scrolling container |
| **Code** | `<pre><code>` inside a collapsed `<details class="code">` (muted ▸ summary, thin left rule): ui-monospace 12.5px, light grey background, 16px padding; keep lines ≤ ~88 chars so nothing scrolls; output in `pre.out`; inline `<code>` for identifiers |
| **Alignment** | left-aligned body (ragged right), never justified |

Implementation notes:
- The article body uses `<body class="wide">`; styles live in `style.css`.
- Stylesheet is linked with a `?v=N` cache-stamp — **bump N whenever `style.css` changes** so GitHub Pages' CDN (10-min cache) serves the new file immediately.
- Figures are hand-authored SVGs in `figures/`; keep internal label text legible at ~560px display width. Interactive figures embed one `<script><![CDATA[...]]></script>` and load via `<object>`; static ones via `<img>`.
- Note: 720px / 16px gives a ~85-char measure — wider than the ~65 "optimal" reading line, but chosen deliberately to match the reference look.

## Writing voice & storytelling

Aim for **Lilian Weng's structure + rigor** with **nrehiew's intuition-first, opinionated delivery**,
carried by the code and numbers above.

**Titles** — descriptive topic phrase, often with a framing lens.
- Good: "The path to 1M context window" · "Looped transformers: what a recurrence is worth" · "Why We Think"

**Subtitle (dek)** — ONE short line, nrehiew's "On X, Y, and Z" shape — name the threads, don't hook.
The opening *paragraph* carries the hook (and ideally the trend/why-now).

**Section headings** — nrehiew style: **Title Case**, phrased as a **claim or question** that
*states the takeaway*, not a topic label. Each heading must **encode the load-bearing "why"**.
Be **specific**: name the mechanism. **No number prefixes** (the TOC numbers them). Don't over-claim.
- Good: "A Recurrence Is Worth About the Square Root of a Fresh Block" · "A Long Window Is Useless If the Model Ignores the Middle" · "Do You Even Need Attention?"

**Structure / how to deliver knowledge**
- Open with a **hook + a unifying frame**: the one mental model the rest of the piece hangs on.
- Build **progressively** — each section earns its place; tighten setup, spend words on what matters.
- Lead with **intuition first, then rigor**: mental model → code or math → numbers → citations.
- **Concrete and quantitative** — real numbers, not hand-waving; say what is measured vs claimed.
- **Cite primary sources inline** as links (`Author et al., year`), like Lilian.
- End with **synthesis** (a recap table or "putting it together").

**Voice**
- Explanatory and accessible, but technically precise — assume a smart reader, don't dumb down.
- **First person is allowed** for intuition and opinion ("the explanation I prefer", "I'd like to know if I'm wrong").
- **Direct address** ("you") and short punchy sentences mixed with fuller explanation.
- **Honest about uncertainty** — flag what's convention vs. measured, what's unverified.
- Opinionated where warranted; take a position and say why.
