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
- Optionally fills file names with sequential suffixes (e.g., `myexport_001`, `myexport_002`).
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

If you ever need a non-interactive run (no Inspector/UI), you can pass `--headless true` **but** you'll also need to remove or guard the `await page.pause();` line in `download_wos_fast5k.js`.

## Usage (PowerShell)

```powershell
node .\download_wos_fast5k.js --base-name "wos_topic_export"
```

Optional flags:

- `--base-name <name>`: optional filename prefix with `_001`, `_002`, etc.
- `--batch-size <n>`: default `5000` (recommended to keep at 5000 for Fast 5K).
- `--headless <true|false>`: default `false`.
- `--timeout-ms <ms>`: default `30000`.
- `--slow-mo <ms>`: default `100`.

## Workflow

1. Script opens Web of Science search page.
2. You manually log in and navigate to your results list.
3. Resume from Playwright inspector pause.
4. Script reads document total.
5. Script loops through computed ranges and exports each batch.
6. Files are saved under `./downloads/`.

## Notes / selector reliability

Web of Science UI labels can vary by tenant or rollout. This script uses robust role/text/CSS fallbacks but may need small selector tweaks if your tenant UI differs.

If range/file inputs are not found, update selectors in:

- `findTotalDocumentCount`
- `openFast5kDialog`
- `setRangeAndFileName`

## Example of final-range handling

If total documents = `6021`, ranges will be:

- `1-5000`
- `5001-6021`

This avoids invalid ranges like `5001-10000` when only 6021 records exist.
