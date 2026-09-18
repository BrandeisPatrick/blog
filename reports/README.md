# reports

Technical reports by [Bat](https://brandeispatrick.github.io/blog/) — benchmarks run
end to end and products taken apart, with the method, the caveats, and the raw
numbers attached. They live in the blog repo, but they are their own site with their
own design — deliberately different from the notes.

**Live:** https://brandeispatrick.github.io/blog/reports/

| Report | Status | Live | Source |
|---|---|---|---|
| **Caveman vs Headroom** — which Claude Code token saver actually saves tokens, and which *kind* | results in (56 Opus runs) | [read](https://brandeispatrick.github.io/blog/reports/skill-gym/) | [`skill-gym/`](skill-gym/) |
| **Devin vs Cursor** — two opposite bets on how an AI should index and retrieve a codebase | pre-test v0, evaluation not yet run | [read](https://brandeispatrick.github.io/blog/reports/devin-vs-cursor/) | [`devin-vs-cursor/`](devin-vs-cursor/) |

## Layout

Each report is a directory that owns everything it needs: a self-contained
`index.html` (no build step, no shared stylesheet — fonts from Google Fonts, all
CSS and figures inline), plus whatever produced it.

```
index.html            landing page — the report index
skill-gym/
  index.html          the report
  gym.py              sandbox-isolated benchmark runner
  analyze.py          event-log → token/cost tables
  fetch_tasks.py      pins benchmark instances
  bin/                deterministic per-task gates
  tasks/              pinned SWE-bench / SpreadsheetBench instances
  results/            summary tables + results.json the page charts
  README.md           method, isolation model, how to run it
devin-vs-cursor/
  index.html          the report
  REPORT.md           the technical report in prose
  PLAN.md             evaluation design: probes, hypotheses, protocol
  research/           annotated primary-source notes with confidence tags
```

Published with the rest of the repo via GitHub Pages, so a report at
`reports/skill-gym/index.html` is served at `/blog/reports/skill-gym/`. The repo-root
`.nojekyll` keeps Pages from touching the files.

## Design

Reports do **not** use the blog's `style.css`, and the blog's `STYLE.md` does not
apply here. They share one design system of their own — paper `#F7F6F5`, Source
Serif 4 / Inter / Geist Mono, 144px sidebar + article grid — and differ only in
`--accent`.

## Add a report

1. Create `your-slug/index.html`. Copying an existing report is the fastest start.
2. Keep the sidebar's `&larr; All reports` back-link pointing at `../`.
3. Add a `<a class="card">` entry to `index.html` here, setting `--ac` inline to
   the report's accent so the card matches the page it opens.
4. Add a row to the table above. Reports are reached from the blog's **Reports** tab;
   they are not listed or linked on the Writing page.

One repo-level wrinkle: the blog's root `.gitignore` drops `*.log`, so
`reports/**/results/*.log` is re-included there — run logs ship as evidence.

## History

These reports lived in a standalone `tech-report` repo (itself a `git subtree` merge
of the earlier `devin-vs-cursor` and `skill-gym` repos) until September 2026, when the
source moved into the blog repo. The harnesses' commit history stays in that repo.
