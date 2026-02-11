# Web of Science Fast 5K Export Automation (Playwright)

This experiment provides a Playwright script that automates downloading Web of Science **Fast 5K** exports in exact 5,000-record batches, including a precise final range.

## What it does

- Assumes you will do manual login and that a search has already been run.
- Detects the total document count from the results page.
- Builds ranges like:
  - `1-5000`
  - `5001-10000`
  - `10001-12034` (final exact range)
- Opens Export → Fast 5K.
- Fills range start/end for each batch.
- Renames downloaded files locally with sequential suffixes (e.g., `myexport_001.txt`, `myexport_002.txt`).
- Downloads each batch using Playwright download handling.

## Script

- `download_wos_fast5k.js`

## Windows setup & run

This script uses `page.pause()` (Playwright Inspector) so you can manually log in before automation continues. That’s simplest in a normal Windows desktop session.

### 1) Install Node.js

- Install Node.js 18+ (LTS) from https://nodejs.org/
- Or via `winget` (PowerShell):

```powershell
winget install OpenJS.NodeJS.LTS
```

### 2) Install Playwright + Chromium

From a PowerShell prompt in this folder:

```powershell
npm i -D playwright
npx playwright install chromium
```

### 3) Run

```powershell
node .\download_wos_fast5k.js --base-name "wos_topic_export" --headless false
```

Downloads are saved under `./downloads/` (on Windows you'll see this as `downloads\\`).

Note: some Web of Science tenants do not provide a filename field in the Fast 5K export dialog. This script does not rely on that UI field; it always saves downloads using a deterministic sequential filename via Playwright.

#### Optional: automated cookie accept + login via `.env`

The script will try to:

- wait briefly for the cookie banner and click **Accept all** (if shown)
- sign in using credentials from a local `.env`

Create a file `wos-fast5k-playwright/.env` with:

```text
WOS_EMAIL=your.email@example.com
WOS_PWD=your-password
```

The repo already ignores `.env` via `.gitignore`.

Notes:

- If your tenant has MFA/SSO flows, the script may still require manual steps.
- After login, you will typically still use the Playwright Inspector pause to run the search and open results.

By default the script does **not** pause after login/search. If you want to manually verify the state (or you have MFA/SSO steps), run with `--pause-after-login true`.

#### Optional: run the Advanced Search automatically from `searchstring.sql`

If `wos-fast5k-playwright/searchstring.sql` exists, the script will read it, fill the **Query Preview** box on the Advanced Search page, and submit the search (Enter first; falls back to clicking a Search button).

This is handy because the Playwright recorder often captures a tokenized URL rather than the actual submit action.

## Usage (PowerShell)

```powershell
node .\download_wos_fast5k.js --base-name "wos_topic_export"
```

Optional flags:

- `--base-name <name>`: optional local filename prefix for saved files (e.g. `myexport_001.txt`). If omitted, the script uses the server-suggested base name (often `savedrecs`).
- `--batch-size <n>`: default `5000` (recommended to keep at 5000 for Fast 5K).
- `--headless <true|false>`: default `false`.
- `--timeout-ms <ms>`: default `60000`.
- `--slow-mo <ms>`: default `100`.
- `--auto-login <true|false>`: default `true` (only runs if `WOS_EMAIL` and `WOS_PWD` are set).
- `--auto-search <true|false>`: default `true` (only runs if `searchstring.sql` is present and non-empty).
- `--search-file <path>`: default `searchstring.sql` (relative to this folder unless absolute).
- `--pause-after-login <true|false>`: default `false`.

## Workflow

1. Script opens Web of Science search page.
2. You manually log in and navigate to your results list.
3. Resume from Playwright inspector pause.
4. Script reads document total.
5. Script loops through computed ranges and exports each batch.
6. Files are saved under `./downloads/`.

## Notes / selector reliability

Web of Science UI labels can vary by tenant or rollout. This script uses robust role/text/CSS fallbacks but may need small selector tweaks if your tenant UI differs.

If the search string is invalid or the search didn’t actually run, the script may fail to detect the total document count. In that case (in headed mode) it will automatically pause so you can fix the query / navigate to the results list, then retry when you resume.

If range/file inputs are not found, update selectors in:

- `findTotalDocumentCount`
- `openFast5kDialog`
- `setRangeAndFileName`

## Example of final-range handling

If total documents = `6021`, ranges will be:

- `1-5000`
- `5001-6021`

This avoids invalid ranges like `5001-10000` when only 6021 records exist.
