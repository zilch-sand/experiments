# Exploring simonw/tools

> **Experiment:** Fork and analyse https://github.com/simonw/tools, then set up a bare-bones version.
> **Date:** 2026-02-24

---

## What is simonw/tools?

[tools.simonwillison.net](https://tools.simonwillison.net) is Simon Willison's collection of small, self-contained browser utilities, almost all written with LLM assistance. The repository is interesting as an infrastructure pattern: it combines a flat folder of HTML files with Python build scripts, LLM-generated documentation, and GitHub Pages + GitHub Actions automation.

---

## Repository structure

```
simonw/tools/
├── .github/
│   └── workflows/
│       ├── pages.yml              ← core build & deploy
│       ├── claude.yml             ← @claude mentions in issues/PRs
│       ├── claude-code-review.yml ← automatic PR reviews by Claude
│       ├── deploy-cloudflare-workers.yml
│       └── test.yml               ← pytest for Python scripts
├── cloudflare-workers/
│   └── github-auth/               ← optional OAuth proxy
├── _config.yml                    ← Jekyll config (theme, title)
├── CNAME                          ← custom domain
├── README.md                      ← the SOURCE for index.html
├── build.sh                       ← orchestrates the Python build
├── gather_links.py                ← produces tools.json
├── build_index.py                 ← README.md → index.html
├── build_colophon.py              ← commit-history page
├── build_dates.py                 ← dates.json
├── build_by_month.py              ← browse-by-month page
├── write_docs.py                  ← LLM doc generation
├── build_redirects.py             ← URL redirect stubs
├── footer.js                      ← footer injected into every tool
├── homepage-search.js             ← live search widget for index
├── tools.json                     ← generated: tool metadata
├── *.html                         ← 60+ tool files (one per tool)
└── *.docs.md                      ← generated: per-tool descriptions
```

### Key design principle
Every tool is a **single self-contained HTML file**. No npm, no bundler, no framework. Tools load third-party libraries from CDNs where needed. This keeps the repo simple and each tool independently deployable.

---

## GitHub Actions

### 1. `pages.yml` – The core CI/CD pipeline

This is the most important workflow. It triggers on every push to `main`:

1. **Checks out full git history** (`fetch-depth: 0`) – this is important because `gather_links.py` uses `git log` to find creation/update dates for each tool.
2. **Installs Python + dependencies** (`markdown`, `llm`, `llm-anthropic`).
3. **Runs `build.sh`**, which in sequence:
   - Runs `gather_links.py` → produces `tools.json` (metadata for all tools)
   - Runs `write_docs.py` (if `GENERATE_LLM_DOCS=1`) → generates/updates `.docs.md` files via Claude Haiku
   - Runs `build_colophon.py` → commit-history page
   - Runs `build_dates.py` → `dates.json`
   - Runs `build_index.py` → converts `README.md` to `index.html` with recently-added/updated sections
   - Runs `build_by_month.py` → browse-by-month page
   - Injects `footer.js` into every `.html` file
   - Runs `build_redirects.py` → creates redirect stub pages
4. **Commits any changed `.docs.md` files** back to the repo.
5. **Deploys to GitHub Pages** via the standard actions/configure-pages → actions/jekyll-build-pages → actions/deploy-pages chain.

### 2. `claude.yml` – Claude Code action

Enables tagging `@claude` in issue bodies, PR comments, or review comments to trigger Claude Code to respond or make changes. Requires a `CLAUDE_CODE_OAUTH_TOKEN` secret.

### 3. `claude-code-review.yml` – Automatic PR reviews

Every time a PR is opened or updated, Claude Code reviews it and posts feedback as a review comment. Also requires `CLAUDE_CODE_OAUTH_TOKEN`.

### 4. `deploy-cloudflare-workers.yml` – OAuth proxy

Some tools (e.g. GitHub API write) need to make authenticated requests. Rather than exposing OAuth secrets client-side, a small Cloudflare Worker acts as a proxy. This workflow deploys that worker when files under `cloudflare-workers/` change. Requires `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` secrets.

### 5. `test.yml` – Python tests

Runs `pytest` on push and PRs to test the Python build scripts themselves.

---

## How the index page works

The index is built in three stages:

### Stage 1: `gather_links.py` → `tools.json`
For each `.html` file in the root directory, the script:
- Runs `git log` to find the earliest (created) and latest (updated) commit dates
- Extracts the `<title>` from the HTML
- Reads the first paragraph from the matching `.docs.md` file (the LLM-generated description)
- Writes all metadata to `tools.json`

```json
[
  {
    "filename": "xml-validator.html",
    "slug": "xml-validator",
    "title": "XML Validator",
    "description": "Validate XML documents directly in your browser...",
    "created": "2024-03-15T10:23:00+00:00",
    "updated": "2024-09-01T14:00:00+00:00",
    "url": "/xml-validator"
  }
]
```

### Stage 2: `build_index.py` → `index.html`
- Reads `README.md` (which contains the manually-maintained list of tools, organised by category)
- Converts it to HTML using the Python `markdown` library
- Finds the `<!-- recently starts -->` / `<!-- recently stops -->` marker comments in the converted HTML
- Injects a "Recently added" / "Recently updated" two-column section between those markers
- Wraps everything in a minimal HTML shell and writes `index.html`

### Stage 3: `homepage-search.js` (client-side)
- This script is referenced in `README.md` as a `<script type="module">` tag
- When the page loads, it fetches `tools.json` and renders a live search box above the tool list
- Searching filters tools by title and description in real time

---

## LLM-generated summaries (`.docs.md`)

### How it works
`write_docs.py` uses the [`llm` CLI](https://llm.datasette.io/) with the `llm-anthropic` plugin to call **Claude Haiku** with a prompt asking for a 2-3 sentence description of each tool.

The prompt (simplified):
> "Write a paragraph of documentation for this page as markdown. Do not include any headings. Keep it to 2-3 sentences. Start with an action verb, not 'This tool is…'"

### Staleness detection
Each generated `.docs.md` file contains a hidden HTML comment:
```
<!-- Generated from commit: abc1234... -->
```
Before regenerating, `write_docs.py` compares this stored hash with the current commit hash of the HTML file. If they match, the file is skipped. This means docs are only re-generated when the tool itself changes – avoiding redundant API calls and unnecessary commits.

### When it runs
Only when the `GENERATE_LLM_DOCS=1` environment variable is set. In the workflow this is only set in CI (with an `ANTHROPIC_API_KEY` secret). You can run it locally too:
```bash
ANTHROPIC_API_KEY=sk-... GENERATE_LLM_DOCS=1 python write_docs.py
```

### Generated docs are committed back
After generating, the workflow commits the new/updated `.docs.md` files back to the repo (`"Generated docs: xml-validator, yaml-explorer"`). This means the docs are stored in git and the index page reads them from disk, not from the API at build time.

---

## Other supporting infrastructure

### `footer.js`
Injected into every tool page by `build.sh`. It:
- Shows a footer with a link back to the index and a link to the colophon (commit history)
- Adapts its colour scheme to match the page background
- Records page visits to `localStorage` for simple analytics

### Cloudflare Workers (`cloudflare-workers/github-auth/`)
Some tools need to make authenticated GitHub API calls. Rather than embedding a client ID/secret in the HTML (visible to all users), a tiny Cloudflare Worker acts as an OAuth callback proxy. The tool redirects to GitHub OAuth → GitHub redirects to the Worker → the Worker exchanges the code for a token and passes it back. This is a well-known pattern for OAuth in single-page apps.

### Custom domain
A `CNAME` file in the repo root tells GitHub Pages to serve at `tools.simonwillison.net`. You need to configure this at your DNS provider too (CNAME record pointing to `<username>.github.io`).

### Jekyll
The repo uses `jekyll-theme-primer` as a minimal theme. Jekyll is used only as a rendering layer by GitHub Pages; the Python build scripts generate `index.html` directly, bypassing Jekyll's templating for that file. Jekyll handles routing (converting `sample-tool.html` → `/sample-tool`).

---

## What you need to set up something similar

### Minimum (GitHub Pages, no LLM)
1. Create a GitHub repository
2. Enable GitHub Pages (Settings → Pages → GitHub Actions source)
3. Add your tool `.html` files to the root
4. Add `README.md` with `<!-- recently starts -->` / `<!-- recently stops -->` markers
5. Add `gather_links.py`, `build_index.py`, `build.sh`, `_config.yml`
6. Add `.github/workflows/pages.yml`
7. Install `pip install markdown` in CI (already in the provided workflow)
8. Push — the workflow builds and deploys automatically

### With LLM summaries
9. Add `write_docs.py` (from simonw's repo or the pattern described above)
10. Add `ANTHROPIC_API_KEY` secret to your GitHub repo
11. Uncomment the LLM section in `pages.yml`

### With Claude Code integration
12. Set up the [Claude Code GitHub App](https://github.com/apps/claude)
13. Add `CLAUDE_CODE_OAUTH_TOKEN` secret
14. Add `.github/workflows/claude.yml` and/or `claude-code-review.yml`

### With custom domain
15. Add a `CNAME` file containing your domain
16. Configure a CNAME DNS record pointing to `<your-username>.github.io`

### With Cloudflare Workers (for OAuth)
17. Create a Cloudflare account and get `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`
18. Add `.github/workflows/deploy-cloudflare-workers.yml`
19. Write your worker code under `cloudflare-workers/<worker-name>/`

---

## Bare-bones version (this folder)

The `bare-bones-site/` subdirectory contains a minimal working template you can use as a starting point:

```
bare-bones-site/
├── .github/
│   └── workflows/
│       └── pages.yml       ← builds and deploys to GitHub Pages
├── _config.yml             ← Jekyll theme config
├── README.md               ← source for index.html (edit this)
├── sample-tool.html        ← example self-contained tool (word counter)
├── gather_links.py         ← produces tools.json from git metadata
├── build_index.py          ← README.md + tools.json → index.html
└── build.sh                ← orchestrates gather_links + build_index
```

### To use it
1. Copy `bare-bones-site/` to a new GitHub repository (as the root)
2. Enable GitHub Pages via Actions in your repo settings
3. Push — the workflow runs automatically and deploys your site
4. Add new tools by creating `.html` files in the root
5. Update `README.md` to list the new tool in the appropriate category

### To add LLM summaries
The `pages.yml` workflow contains a commented-out section for LLM docs generation. To enable:
1. Add `ANTHROPIC_API_KEY` as a repository secret
2. Download `write_docs.py` from [simonw/tools](https://github.com/simonw/tools/blob/main/write_docs.py)
3. Uncomment the relevant block in `pages.yml`

---

## Key insights

1. **Simplicity is the point.** No build toolchain, no framework, no npm. Each tool is just HTML. This means you can create tools quickly with an LLM and they work instantly in a browser.

2. **`README.md` as the source of truth.** The index page is generated from README.md, so the list of tools is maintained as plain markdown. Easy to edit, easy to read on GitHub.

3. **LLM docs as a build artefact.** The descriptions are generated once (when the tool changes), committed back to git, and read from disk during the next build. No API calls at deploy time.

4. **Full git history matters.** The `fetch-depth: 0` in the checkout step is critical — without it, creation dates would be wrong or missing.

5. **Jekyll is used minimally.** Only for its GitHub Pages integration and theme. The real HTML generation is done by Python scripts.

6. **Claude Code integration is optional but powerful.** With just one workflow file and a secret, you get AI-assisted development directly in your GitHub issues and PRs.

---

## References

- [simonw/tools repository](https://github.com/simonw/tools)
- [tools.simonwillison.net](https://tools.simonwillison.net)
- [Simon's blog post on one-shot Python tools](https://simonwillison.net/2024/Dec/19/one-shot-python-tools/)
- [llm CLI tool](https://llm.datasette.io/)
- [Claude Code GitHub Action](https://github.com/anthropics/claude-code-action)
- [GitHub Pages documentation](https://docs.github.com/en/pages)
