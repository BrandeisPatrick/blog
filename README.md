# BrandeisPatrick.github.io

My personal notebook. Plain HTML + CSS, no build step, hosted free on GitHub Pages.
Live at **https://brandeispatrick.github.io**.

## How it's built

- **No framework, no build.** Every page is a static `.html` file you can open directly.
- **One stylesheet** (`style.css`) — a single readable column, system fonts, light/dark via `prefers-color-scheme`.
- **[Pretext](https://github.com/chenglou/pretext)** powers the freely-arranged hero tagline on the homepage (loaded from a CDN, progressively enhanced — the page works fine without it).

## Add a post

1. Copy an existing file in `posts/` to `posts/your-slug.html`.
2. Edit the title, date, and body.
3. Add a `<article class="post-link">` entry near the top of `index.html` so it shows in the list.
4. Commit and push — GitHub Pages redeploys automatically.

## Run locally

Just open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server
# then visit http://localhost:8000
```
