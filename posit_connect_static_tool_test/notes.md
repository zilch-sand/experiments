# Notes

## 2026-02-23

- Investigated browser error in `static_html/posit_connect_static_tool_stress_test_single_html.html`:
  - `Uncaught SyntaxError: await is only valid in async functions and the top level bodies of modules`
- Root cause: a duplicated fragment of fetch-handling code remained after the `btnProxy` event listener, leaving `await` statements outside an async function.
- Fix: removed the stray duplicated block immediately after the proxy listener closure.
- Result: script structure is valid again; `await` is now used only inside async event handlers.

- Follow-up for Posit Connect deployment pathing:
  - Updated proxy URL construction from absolute root (`/api/proxy`) to page-relative (`new URL('api/proxy', window.location.href)`).
  - This supports Connect-style paths like:
    `https://connect.it.csiro.au/content/<guid>/...` → `https://connect.it.csiro.au/content/<guid>/api/proxy?...`
  - Avoids hard-coding the host or content GUID in the HTML.

- Follow-up for separate proxy deployment:
  - Added a new `Proxy endpoint` input in the UI.
  - Proxy fetch now resolves from that configured endpoint (`new URL(endpoint, window.location.href)`) and appends `?url=...`.
  - This supports either:
    - relative endpoint (same deployment), or
    - full absolute endpoint for another Connect deployment, e.g.
      `https://connect.it.csiro.au/content/<other-guid>/api/proxy`

- Consolidation into one deployment path:
  - Updated `fastapi_proxy/app.py` to serve the HTML UI at `/` and `/index.html`.
  - Kept proxy API at `/api/proxy` in the same app.
  - Updated HTML proxy default to `api/proxy` so it resolves correctly under Connect content paths.

- FastAPI proxy timeout fix:
  - Investigated runtime error: `ValueError: httpx.Timeout must either include a default, or set all four parameters explicitly`.
  - Root cause: timeout was constructed with only `connect` and `read` and no default.
  - Fix: changed to `httpx.Timeout(20.0, connect=10.0)` so a default is set while keeping a stricter connect timeout.
  - Result: proxy client construction no longer raises this `ValueError`.

- Deployment file-not-found troubleshooting (this iteration):
  - Symptom from deployment flow: failure during file preparation / bundle creation and runtime inability to find `index.html`.
  - Root cause #1 (publisher config): `.posit/publish/posit_connect_static_tool_test-TETO.toml` listed files with leading slashes (`/app.py`, etc.), which can break relative file resolution during bundling.
  - Fix #1: switched file list to relative paths (`app.py`, `requirements.txt`, `static/index.html`).
  - Root cause #2 (runtime path): `app.py` computed `BASE_DIR` as `Path(__file__).resolve().parent.parent`, which points one directory too high for this layout.
  - Fix #2: changed to `Path(__file__).resolve().parent` so the app serves `static/index.html` from the deployment folder.
  - Result: deployment packaging and runtime static file lookup now align with the project structure.

- README refinement (this iteration):
  - Rewrote `README.md` to focus on current purpose and operating model, removing implementation-history and change-log style details.
  - Added clearer sections for:
    - what the experiment is trying to prove,
    - what each module tests and why it matters,
    - what works vs what fails in this environment,
    - why the `/api/proxy` endpoint is needed on Connect.
  - Framed conclusions around observed CSP/frame restrictions and the same-origin proxy pattern for external data access.
