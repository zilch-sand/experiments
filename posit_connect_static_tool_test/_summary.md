Hosting single-file, browser-heavy HTML tools on [Posit Connect](https://posit.co/products/connect/) is practical for most local page functionality, provided the current content security policy (CSP) allows inline scripting and standard browser APIs. The main obstacles observed in this stress-test are direct external API calls—blocked by CSP `connect-src`—and generic iframe embedding, which fails due to both host and target frame restrictions. Deploying a backend proxy API (e.g., [FastAPI](https://fastapi.tiangolo.com/)), which relays external requests server-side, reliably circumvents browser-side CORS and CSP blocks, but inherits any server/network egress constraints. Overall, feature-rich single-page tools can thrive if external integration is handled via a local proxy pattern.

**Key findings:**
- Core client-side behaviors (inline JS, localStorage, file input) work reliably within page origin.
- Direct browser calls to external APIs and generic iframes are restricted by CSP and frame policies.
- Integrating a proxy API enables controlled outbound requests with centralized access control.
- Server/network egress rules can still restrict external access even when using a proxy.
