# blog

My personal notebook. Plain HTML + CSS, no build step, hosted free on GitHub Pages.
Live at **https://brandeispatrick.github.io/blog/**.

## How it's built

- **No framework, no build.** Every page is a static `.html` file you can open directly.
- **One stylesheet** (`style.css`) — a single readable column, system fonts, a fixed light theme.
- **[Pretext](https://github.com/chenglou/pretext)** powers the freely-arranged hero tagline on the homepage (loaded from a CDN, progressively enhanced — the page works fine without it).

## Add a post

1. Copy an existing file in `posts/` to `posts/your-slug.html`.
2. Edit the title, date, and body.
3. Add a `<article class="post-link">` entry to `index.html`:
   - **Still writing?** Put it in the **"On the desk"** section (the folded
     `<details>` at the bottom of the homepage — collapsed by default) with a
     `<span class="status">Draft — …</span>` tag, and update the draft count in
     its `<summary>` line.
   - **Done?** Put it in the main list at the top, and drop the draft tag.
4. Commit and push — GitHub Pages redeploys automatically.

Posts keep the same URL either way — publishing is just moving the entry between
sections on the homepage.

## Run locally

Just open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server
# then visit http://localhost:8000
```
