# Posit Connect static tool stress-test (single HTML)

## Goal

A single-page HTML file that intentionally uses common “static tool” patterns that can break on enterprise platforms (including Posit Connect behind SSO / reverse proxies) due to:

- Content Security Policy (CSP)
- network/proxy egress restrictions
- browser permissions (clipboard, storage)
- sandboxing / embedding restrictions

Use it to answer: **“Can I host Simon-style HTML tools on Connect and what will be restricted?”**

---

## How to run

1. Save the HTML as `connect_static_stress_test.html`.
2. Host it:
   - on Posit Connect (your preferred “static content” method), and/or
   - locally (open the file, or serve with a tiny static server).
3. Open browser DevTools:
   - **Console**: CSP/CORS/permission errors will show here.
   - **Network**: confirm requests/scripts are actually loading.
4. Click through each section and note what passes/fails.

**Tip:** Most “it works locally but not on Connect” failures are CSP headers injected by Connect or a proxy in front of it.

---

## What we’re testing

### Baseline: inline script + inline style
The page includes inline `<style>` and inline `<script>`.

**Tests**
- CSP `script-src` allowing inline scripts (via `'unsafe-inline'` or nonces/hashes)
- CSP `style-src` allowing inline styles

**Failure symptoms**
- Buttons do nothing / page feels inert
- Console shows CSP violations referencing inline scripts/styles

---

## Test modules

### 1) Inline JS + URL state
**What it does**
- Reads `?q=...` from the URL on load and populates an input.
- “Update URL” uses `history.replaceState()` to update `?q=` without reloading.
- “Read URL” re-parses the URL and prints `q`.

**Tests**
- Basic JS execution
- URL state manipulation

**Common failures**
- Rare if inline JS is permitted.

---

### 2) `localStorage`
**What it does**
- Save / load / clear a key/value pair in `localStorage`.

**Tests**
- Whether persistent storage is allowed under the site origin

**Common failures**
- Storage blocked by browser privacy settings
- Storage blocked in certain embedded/sandboxed contexts

---

### 3) Public API fetch (cross-origin)
**What it does**
Calls one of:
- `https://api.github.com/zen` (text)
- `https://worldtimeapi.org/api/ip` (JSON)
- `https://httpbin.org/get` (JSON)

Displays HTTP status + response body.

**Tests**
- CORS for cross-origin requests
- CSP `connect-src` restrictions
- Network/proxy allowlists and DNS egress

**Failure symptoms**
- Console: `Refused to connect ... because it violates the document's Content Security Policy`
- Console: `Blocked by CORS policy`
- Network: request never leaves / ERR_* failures / 403 via proxy

---

### 4) Clipboard + File input

#### Clipboard
**What it does**
- “Copy”: `navigator.clipboard.writeText()`
- “Paste”: `navigator.clipboard.readText()`

**Tests**
- HTTPS + permission gating + “user gesture” requirements
- Whether clipboard APIs are blocked by policy

**Failure symptoms**
- Errors like `NotAllowedError` (permissions / gesture)
- Works in some browsers but not others

#### File input
**What it does**
- Reads the first ~100KB of a chosen local file via `File.arrayBuffer()` + `TextDecoder`.

**Tests**
- Local file handling APIs

**Failure symptoms**
- Rare; usually works unless the environment is heavily sandboxed.

---

### 5) CDN script load + DOM sanitization
**What it does**
- Loads **DOMPurify** via CDN:  
  `https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js`
- Lets you paste “untrusted HTML”, sanitizes it, and renders the safe result.

**Tests**
- CSP `script-src` allowing third-party origins (jsDelivr)
- Network egress to the CDN
- Whether external scripts are blocked by proxy/security

**Failure symptoms**
- `DOMPurify not present (CDN blocked?)`
- Console CSP errors about `script-src`
- Network tab shows the CDN request blocked/failed

**Note**
- This experiment intentionally does **not** use SRI (`integrity=`). A bad SRI hash will make the script fail even locally and would confound results.

---

### 6) Web Worker from `blob:` URL
**What it does**
- Creates a worker from a Blob URL (`blob:`) and runs a simple “sum 1..N” computation.

**Tests**
- CSP `worker-src`
- Whether `blob:` is allowed for workers (sometimes blocked)
- Worker execution in the environment

**Failure symptoms**
- Console CSP error referencing `worker-src` or `blob:`
- Worker fails immediately / “blocked”

---

### 7) `iframe` embedding
**What it does**
- Attempts to embed a URL in an `<iframe>` (default `https://example.com`).

**Tests**
- Target site framing headers (`X-Frame-Options` / `Content-Security-Policy: frame-ancestors`)
- Any platform-level restrictions on framing

**Failure symptoms**
- Blank iframe
- Console errors like:
  - “Refused to display … in a frame because it set ‘X-Frame-Options’…”
  - CSP `frame-ancestors` violations

---

## Interpreting results quickly

- **Inline script/style failures** → CSP is strict (no `'unsafe-inline'` / missing nonces).
- **CDN script fails** → CSP `script-src` doesn’t allow CDN, or egress/proxy blocks it.
- **Fetch fails** → CSP `connect-src` and/or proxy egress and/or CORS.
- **Worker fails** → CSP `worker-src` (often needs `blob:` allowed).
- **Clipboard fails** → browser permission / HTTPS / user gesture policies.

---

## Results

Rount 1:
**Failures**:
- External APIs failed due to CSP restrictions. 
`Connecting to 'https://api.github.com/zen' violates the following Content Security Policy directive: "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com https://posit-dev.github.io https://raw.githubusercontent.com https://*.mapbox.com https://cdn.plot.ly https://cdn.quarto.org https://tile.openstreetmap.org https://a.tile.openstreetmap.org https://b.tile.openstreetmap.org https://c.tile.openstreetmap.org https://*.csiro.au". The action has been blocked.`
- iframe embedding failed due to CSP.
`Framing 'https://example.com/' violates the following Content Security Policy directive: "frame-src 'self' https://login.microsoftonline.com https://storymaps.arcgis.com". The request has been blocked.`