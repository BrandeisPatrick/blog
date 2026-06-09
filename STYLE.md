# Blog style guide

The style this blog should follow — both **visual design** and **writing voice**.
Reference blogs: [Lilian Weng](https://lilianweng.github.io/posts/2025-05-01-thinking/)
and [nrehiew / wh](https://nrehiew.github.io/blog/sft_rl_opd/).

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
| **Figures** | **small & centered** (~560px, ~78% of column), **no border**, centered grey caption (13px). Lead caption with bold `Figure N — Title.` |
| **Alignment** | left-aligned body (ragged right), never justified |

Implementation notes:
- The article body uses `<body class="wide">`; styles live in `style.css`.
- Stylesheet is linked with a `?v=N` cache-stamp — **bump N whenever `style.css` changes** so GitHub Pages' CDN (10-min cache) serves the new file immediately.
- Figures are hand-authored SVGs in `figures/`; keep internal label text legible at ~560px display width.
- Note: 720px / 16px gives a ~85-char measure — wider than the ~65 "optimal" reading line, but chosen deliberately to match the reference look.

## Writing voice & storytelling

Aim for the blend of the two reference blogs: **Lilian Weng's structure + rigor**
with **nrehiew's intuition-first, opinionated delivery.**

**Titles** — descriptive topic phrase, often with a framing lens.
- Good: "The path to 1M context window" · "SFT, RL, and On-Policy Distillation Through a Distributional Lens" · "Why We Think"

**Subtitle (dek)** — ONE short line, nrehiew's "On X, Y, and Z" shape — name the threads, don't hook.
Not a paragraph. The opening *paragraph* carries the hook (and ideally the trend/why-now).
- Good: "On positional encoding, the KV cache, attention, and everything else that had to change to read a million tokens."

**Section headings** — nrehiew style: **Title Case**, phrased as a **claim or question** that
*states the takeaway*, not a topic label. Each heading must **encode the load-bearing "why"** —
for a long-context piece, *why this matters when the context gets long*. Be **specific**: name the
mechanism (N²/N scaling, RoPE-vs-NoPE), don't gesture vaguely ("keep it where it helps" = too vague;
"RoPE for Local Order, NoPE for Long-Range Reach" = good). **No number prefixes** (the TOC numbers them).
Don't over-claim — a heading shouldn't imply its section explains the whole topic.
- Good: "Why Length Is Expensive: Attention Scales as N², Memory as N" · "A Long Window Is Useless If the Model Ignores the Middle" · "Do You Even Need Attention?"
- Lilian's plainer noun-label style ("Latent Variable Modeling") is the alternative, but it can't carry a "why" — use nrehiew's for this blog.

**Structure / how to deliver knowledge**
- Open with a **hook + a unifying frame**: state the one mental model or "the whole game is X"
  that the rest of the piece hangs on. (e.g. "everything below is an attack on one of two costs.")
- Build **progressively** — each section earns its place; tighten setup, spend words on what matters.
- Lead with **intuition first, then rigor**: give the mental model, then the math/numbers/citations.
- **Concrete and quantitative** — real numbers, not hand-waving.
- **Cite primary sources inline** as links (`Author et al., year`), like Lilian.
- **Figures carry key comparisons** — small, centered, captioned `Figure N — …`.
- End with **synthesis** (a recap table or "putting it together").

**Voice**
- Explanatory and accessible, but technically precise — assume a smart reader, don't dumb down.
- **First person is allowed** for intuition and opinion ("the explanation I prefer", "I'd like to know if I'm wrong").
- **Direct address** ("you") and short punchy sentences mixed with fuller explanation.
- **Honest about uncertainty** — flag what's convention vs. measured, what's unverified.
- Opinionated where warranted; take a position and say why.
