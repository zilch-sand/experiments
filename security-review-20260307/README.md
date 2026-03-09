# Security Review

Reviewed on 2026-03-07 for `/home/runner/work/experiments/experiments`.

## Scope and method

This review covered the repository’s tracked experiments, with emphasis on:

- externally reachable HTTP endpoints
- file-system writes and deletes
- subprocess execution
- secret handling
- generated HTML/content rendering
- GitHub Actions permissions

The assessment used semantic code search, direct source inspection, and the repository’s existing automated tests where available.

## Baseline validation

### Automated tests

`llm-classification-app` is the only project in this repository with committed automated tests.

- Attempting `python -m pip install -e .` in `llm-classification-app` currently fails because setuptools auto-discovers both `backend` and `batch_state` as top-level packages.
- After installing the minimal test dependencies manually, `PYTHONPATH=. python -m pytest tests/ -v` ran successfully enough to establish a baseline:
  - **43 passed**
  - **2 failed (pre-existing)** in `tests/test_prompt.py`
  - The failures are expectation mismatches for newline-separated vs comma-separated `label_options`, not security failures.

### Positive security observations

- Root `.gitignore` excludes `.env`, reducing the chance of committing local secrets.
- `posit_connect_static_tool_test/app.py` restricts the initial proxy destination to an allowlist and caps response bodies at 1,000,000 bytes.
- `simonw-tools-exploration/bare-bones-site/gather_links.py` invokes `git` with an argument list rather than `shell=True`.
- `.github/workflows/update-readme.yml` is limited to `push` on `main` and requests only `contents: write` and `models: read`.

## Findings

### 1. Allowlist bypass via followed redirects in proxy demo

- **Severity:** Medium
- **File:** `/home/runner/work/experiments/experiments/posit_connect_static_tool_test/app.py:33-69`

#### Why it matters

The proxy endpoint validates the **original** `url` host against `ALLOWED_HOSTS`, but the outbound client is configured with:

```python
async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
```

That means an allowed host can redirect the server to another host that is **not** in `ALLOWED_HOSTS`, and the code will still fetch it. In practice, this weakens the allowlist and can turn the endpoint into a limited SSRF primitive if any allowed host can issue attacker-controlled redirects.

#### Recommendation

- Prefer `follow_redirects=False` for this endpoint, or
- intercept each redirect and re-validate the destination host before following it.

---

### 2. Unsanitized `batch_id` used in file paths

- **Severity:** Medium
- **File:** `/home/runner/work/experiments/experiments/llm-classification-app/backend/batch.py:24-48,63-67`

#### Why it matters

Batch tracking persists state using paths built directly from `batch_id`:

```python
filepath = BATCH_STATE_DIR / f"{batch_id}.json"
```

The same pattern is used for save, update, and cleanup. If `batch_id` ever becomes attacker-controlled or comes from an unexpected upstream source, values containing path separators such as `../` could escape the intended directory and overwrite or delete arbitrary files reachable from the app’s working tree.

Current usage suggests batch IDs are expected to come from trusted APIs, so exploitability may be constrained today, but the sink itself is unsafe.

#### Recommendation

- Validate `batch_id` against a strict allowlist regex, such as `^[A-Za-z0-9._-]+$`, and/or
- resolve the final path and reject it unless it remains under `BATCH_STATE_DIR`.

---

### 3. Generated site embeds Markdown-derived HTML without sanitization

- **Severity:** Low to Medium
- **File:** `/home/runner/work/experiments/experiments/simonw-tools-exploration/bare-bones-site/build_index.py:97-138`

#### Why it matters

`build_index.py` converts `README.md` to HTML using Python-Markdown and then interpolates the result directly into the output page:

```python
md = markdown.Markdown(extensions=["extra"])
body_html = md.convert(md_text)
...
html = f"""... {body_html} ..."""
```

If untrusted Markdown or raw HTML is ever allowed into `README.md`, the generated site can publish executable markup. If the repository content is fully trusted, this is lower risk; if community-authored content is published automatically, the exposure increases.

#### Recommendation

- Sanitize the rendered HTML before writing it, or
- enforce a restrictive Content Security Policy when serving the generated page, or
- limit accepted Markdown/HTML features if the content source becomes less trusted.

---

### 4. Broad development CORS policy

- **Severity:** Low
- **File:** `/home/runner/work/experiments/experiments/pydantic-jsonforms-demo/app.py:51-63`

#### Why it matters

The demo API allows credentials together with wildcard methods and headers:

```python
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
```

Because `allow_origins` is restricted to localhost development origins, the current risk is limited. Still, this is broader than necessary and could become problematic if the config is copied into a less constrained deployment.

#### Recommendation

- Narrow methods to the specific verbs in use.
- Narrow headers to the ones the frontend actually needs.
- Keep this configuration explicitly documented as development-only.

---

### 5. Local password-based automation relies on operator secret hygiene

- **Severity:** Low
- **Files:** 
  - `/home/runner/work/experiments/experiments/wos-fast5k-playwright/download_wos_fast5k.js:436-462`
  - `/home/runner/work/experiments/experiments/.gitignore:11`

#### Why it matters

The Playwright automation reads `WOS_EMAIL` and `WOS_PWD` from a local `.env` file. The repo does ignore `.env`, which is good, so this is not a committed-secret issue in the current state. The residual risk is operational: local plaintext secrets are easy to mishandle, reuse, or leak through logs or workstation compromise.

#### Recommendation

- Keep `.env` local only and never echo credentials.
- Prefer shorter-lived credentials or a secret manager if this script moves beyond personal/local use.

## Overall assessment

No critical repository-wide secret exposure or shell-injection pattern was found in the reviewed code. The most important concrete issue is the proxy endpoint’s redirect behavior, followed by the unsafe path construction in batch state persistence.

If remediation work is planned, the most valuable next steps are:

1. Harden `posit_connect_static_tool_test/app.py` against redirect-based allowlist bypass.
2. Sanitize or constrain `batch_id` before using it in filesystem paths.
3. Decide whether the static site generator should treat Markdown as trusted or sanitize rendered HTML defensively.

## Deliverable note

This issue requested a security review. No application code was modified as part of this work; the change set is limited to this review folder and its documentation.
