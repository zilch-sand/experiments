# Posit Connect static tool stress-test (single HTML)

## What this is trying to do

This project is a practical compatibility check for hosting a single-file, browser-heavy HTML tool on Posit Connect.

The core question is:
**Can we host Simon-style static HTML tools on Connect, and what platform/security constraints matter in practice?**

It is intentionally built as a stress-test, not a polished app.

---

## How it is deployed

Recommended setup is one FastAPI deployment that serves both:

- UI: `GET /` (or `/index.html`)
- Proxy API: `GET /api/proxy?url=...`

When deployed on Connect, both routes live under the same content path (for example `/content/<guid>/...`).
The UI defaults the proxy endpoint to `api/proxy` so it stays path-relative.

Implementation:

- API app: `fastapi_proxy/app.py`
- HTML UI: `static_html/posit_connect_static_tool_stress_test_single_html.html`

---

## What we test and why

Each module maps to a real enterprise failure mode:

1. **Inline script + style**
  - Tests whether CSP allows inline JavaScript/CSS.
  - Why: many single-file tools rely on inline blocks.

2. **URL state (`history.replaceState`)**
  - Tests basic client-side state behavior.
  - Why: lightweight tools often encode state in query params.

3. **`localStorage`**
  - Tests browser storage under deployed origin.
  - Why: simple persistence without backend.

4. **Cross-origin public API fetch**
  - Tests browser CORS + CSP `connect-src` + egress constraints.
  - Why: many tools pull external data directly from the browser.

5. **Clipboard + file input APIs**
  - Tests browser permission-gated APIs and local file read behavior.
  - Why: user workflows often involve copy/paste and uploading files.

6. **CDN script load (DOMPurify)**
  - Tests third-party script loading under CSP/network policy.
  - Why: static tools commonly depend on CDN-hosted libraries.

7. **Web Worker from `blob:` URL**
  - Tests `worker-src` and `blob:` allowance.
  - Why: offloading heavier computation to workers is common.

8. **`iframe` embedding**
  - Tests frame restrictions (`X-Frame-Options`, `frame-src`, `frame-ancestors`).
  - Why: tools may need to embed external pages or dashboards.

---

## What works

In this environment, core in-page/browser-local functionality is generally viable:

- Inline JS and page interactions (assuming current CSP allows inline execution)
- URL read/update behavior
- Local browser features like `localStorage` (subject to browser/privacy mode)
- File input reading

These are usually stable because they stay within the page origin and do not require external network access.

---

## What does not work (and why)

### Direct external API calls from the browser

Direct calls to endpoints like `https://api.github.com/zen` were blocked by CSP (`connect-src`).

Why this fails:

- Browser is enforcing page CSP headers from Connect/proxy.
- External domains are not in allowed `connect-src` list.
- Even when DNS/network is reachable, CSP can still block before request completion.

### External iframe embedding (for generic URLs)

Embedding `https://example.com` in an iframe was blocked due to frame policy restrictions.

Why this fails:

- `frame-src` restrictions on the host page and/or
- target-site anti-framing headers (`X-Frame-Options` / `frame-ancestors`).

---

## Why the API proxy is needed

The proxy exists to move external fetches from **browser-side cross-origin requests** to a **same-origin app request**:

1. Browser calls `GET /api/proxy?url=...` on the same deployment origin.
2. Server performs outbound HTTP request.
3. Server returns response back to UI.

This helps because:

- Browser CORS restrictions no longer apply to the external target (browser only talks to same origin).
- Browser `connect-src` can remain narrow (`'self'`) while still enabling controlled external access via backend.
- Access control, allowlisting, logging, and sanitization can be centralized server-side.

Important caveat: server-side egress policies still apply. If Connect/network policy blocks outbound traffic, proxy calls can still fail.

---

## Quick usage

1. Deploy or run `fastapi_proxy/app.py`.
2. Open the app root (`/`).
3. Keep **Proxy endpoint** as `api/proxy` for same-deployment mode.
4. Use browser DevTools:
  - **Console** for CSP/CORS/permission errors
  - **Network** to verify which requests are blocked vs completed

---

## Bottom line

Single-file static tools are feasible on Connect for local/browser-native behavior.
The main limitations are external network access and iframe embedding, both commonly constrained by CSP/security policy.
For external data access, a same-deployment proxy API is the reliable pattern.