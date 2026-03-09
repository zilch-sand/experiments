# Notes

- Started security review on 2026-03-07.
- Ran semantic search first to identify projects, likely test commands, and security-sensitive files.
- Confirmed the repository root contains multiple independent experiments; only `llm-classification-app` has committed automated tests.
- Verified directly from source:
  - `posit_connect_static_tool_test/app.py` validates the initial proxy URL host but uses `httpx.AsyncClient(..., follow_redirects=True)`.
  - `llm-classification-app/backend/batch.py` uses raw `batch_id` values in file paths for save/update/delete operations.
  - `pydantic-jsonforms-demo/app.py` enables `allow_credentials=True` with wildcard methods/headers for localhost origins.
  - `simonw-tools-exploration/bare-bones-site/build_index.py` renders Markdown to HTML and writes the result directly into the generated page.
  - `wos-fast5k-playwright/download_wos_fast5k.js` reads `WOS_EMAIL`/`WOS_PWD` from a local `.env`.
- Verified mitigations already present:
  - Root `.gitignore` excludes `.env`.
  - The proxy demo caps upstream response bodies at 1,000,000 bytes.
  - `gather_links.py` uses `subprocess.run([...])` without `shell=True`.
- Baseline validation:
  - `python -m pytest tests/ -v` initially failed because `pytest` was not installed.
  - `uv` is not available in this sandbox.
  - `python -m pip install -e .` fails in `llm-classification-app` because setuptools discovers both `backend` and `batch_state` as top-level packages.
  - After installing minimal test dependencies manually, `PYTHONPATH=. python -m pytest tests/ -v` in `llm-classification-app` completed with 43 passing tests and 2 pre-existing failures in `tests/test_prompt.py` (`test_render`, `test_preview_uses_first_row`) due to newline-vs-comma expectations for `label_options`.
