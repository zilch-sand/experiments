# Notes

## 2026-02-10
- Created a new experiment folder `wos-fast5k-playwright`.
- Implemented a Playwright automation script in Node.js to:
  - Wait for manual login/search confirmation using `page.pause()`.
  - Read total document count from likely result text patterns and fall back to regex against page body text.
  - Compute exact export ranges in 5,000-document batches where the final batch uses the exact total count (e.g., `5001-6021`).
  - Open the Export menu and select the `Fast 5K` option using role/text fallbacks.
  - Fill start/end range fields and optionally populate a sequential filename suffix (`_001`, `_002`, ...).
  - Trigger and save downloads from the browser download event.
- Added CLI options for:
  - `--base-name`
  - `--batch-size` (defaults to 5000)
  - `--headless`
  - `--timeout-ms`
  - `--slow-mo`
- Validation done locally with `node --check` to ensure script syntax is valid.
- No live run against Web of Science was performed in this environment due needing interactive login and account-backed data.
