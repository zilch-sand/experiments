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

## 2026-02-11
- Added a minimal `.env` loader (no additional npm dependencies) and startup automation steps:
  - short startup wait then click **Accept all** on the cookie banner if present
  - optional Sign In flow using `WOS_EMAIL` and `WOS_PWD` from `.env`
- Kept the interactive workflow: after login, the script still pauses so the user can run the search and open the results list.
- Added CLI flags:
  - `--auto-login <true|false>`
  - `--pause-after-login <true|false>`
- Added optional auto-search:
  - reads the query from `searchstring.sql`
  - fills the Advanced Search **Query Preview** textbox
  - submits via Enter (fallback to clicking a Search button)
  - adds CLI flags `--auto-search` and `--search-file`
- Changed `--pause-after-login` default to `false` now that query entry/search can be automated.
- Added a conditional recovery pause: if total document count detection fails (often due to an invalid/unsubmitted query), the script pauses to let the user fix the search, then retries when resumed.
- Implemented deterministic local renaming of downloads using Playwright `saveAs()` with sequential numbering; no longer depends on a filename input in the Fast 5K export form (often absent).
- Added a small normalization step when reading `searchstring.sql`: fixes formatter-introduced spaces in year ranges like `FPY = 2020 -2024` → `FPY = 2020-2024` (writes the corrected file back to disk).
- Extended the normalization step to also fix wildcard spacing like `energ *` → `energ*` (i.e., replaces literal ` *` with `*`).
