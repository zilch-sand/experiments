#!/usr/bin/env node
/**
 * Automate Web of Science "Fast 5K" exports in exact 5,000-document batches.
 *
 * Assumptions:
 * - User performs login manually.
 * - A search is already run and result list is open.
 * - The page supports Fast 5K export with a custom record range.
 *
 * Usage:
 *   node download_wos_fast5k.js --base-name "my_wos_export"
 *   node download_wos_fast5k.js --headless false
 */

const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

function loadDotEnv(dotEnvPath) {
  // Minimal .env loader (avoids adding npm deps). Values are only loaded if the
  // variable is not already defined in the environment.
  try {
    if (!fs.existsSync(dotEnvPath)) return;
    const raw = fs.readFileSync(dotEnvPath, 'utf8');
    const lines = raw.split(/\r?\n/);

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;

      const noExport = trimmed.startsWith('export ') ? trimmed.slice('export '.length) : trimmed;
      const eqIdx = noExport.indexOf('=');
      if (eqIdx <= 0) continue;

      const key = noExport.slice(0, eqIdx).trim();
      if (!key) continue;

      let val = noExport.slice(eqIdx + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }

      if (process.env[key] == null || process.env[key] === '') {
        process.env[key] = val;
      }
    }
  } catch (err) {
    console.warn(`Warning: failed to load .env from ${dotEnvPath}: ${err.message}`);
  }
}

function parseArgs(argv) {
  const args = {
    headless: false,
    batchSize: 5000,
    baseName: '',
    timeoutMs: 60_000,
    slowMo: 100,
    autoLogin: true,
    autoSearch: true,
    searchFile: 'searchstring.sql',
    pauseAfterLogin: false,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--headless') {
      args.headless = argv[i + 1] !== 'false';
      i += 1;
    } else if (arg === '--batch-size') {
      const val = Number(argv[i + 1]);
      if (Number.isFinite(val) && val > 0 && val <= 50000) {
        args.batchSize = val;
      } else {
        throw new Error('--batch-size must be a positive number <= 50000');
      }
      i += 1;
    } else if (arg === '--base-name') {
      // Sanitize to prevent path traversal
      const raw = argv[i + 1] || '';
      args.baseName = path.basename(raw);
      if (raw !== args.baseName && raw !== '') {
        console.warn(`Warning: base-name sanitized from "${raw}" to "${args.baseName}"`);
      }
      i += 1;
    } else if (arg === '--timeout-ms') {
      const val = Number(argv[i + 1]);
      if (Number.isFinite(val) && val >= 0 && val <= 300000) {
        args.timeoutMs = val;
      } else {
        throw new Error('--timeout-ms must be a number between 0 and 300000');
      }
      i += 1;
    } else if (arg === '--slow-mo') {
      const val = Number(argv[i + 1]);
      if (Number.isFinite(val) && val >= 0 && val <= 5000) {
        args.slowMo = val;
      } else {
        throw new Error('--slow-mo must be a number between 0 and 5000');
      }
      i += 1;
    } else if (arg === '--auto-login') {
      args.autoLogin = argv[i + 1] !== 'false';
      i += 1;
    } else if (arg === '--auto-search') {
      args.autoSearch = argv[i + 1] !== 'false';
      i += 1;
    } else if (arg === '--search-file') {
      args.searchFile = argv[i + 1] || args.searchFile;
      i += 1;
    } else if (arg === '--pause-after-login') {
      args.pauseAfterLogin = argv[i + 1] !== 'false';
      i += 1;
    }
  }

  return args;
}

function batchRanges(total, batchSize) {
  const ranges = [];
  for (let start = 1; start <= total; start += batchSize) {
    const end = Math.min(start + batchSize - 1, total);
    ranges.push({ start, end });
  }
  return ranges;
}

async function findTotalDocumentCount(page) {
  const candidateLocators = [
    page.getByText(/\b\d{1,3}(?:,\d{3})*\s+documents?\b/i),
    page.getByText(/\bdocuments?\s*\(\s*\d{1,3}(?:,\d{3})*\s*\)/i),
    page.getByText(/\bresults?\s*\(\s*\d{1,3}(?:,\d{3})*\s*\)/i),
    page.getByText(/\bof\s+\d{1,3}(?:,\d{3})*\b/i),
  ];

  for (const locator of candidateLocators) {
    const count = await locator.count();
    if (count > 0) {
      const text = (await locator.first().innerText()).trim();
      const numbers = text.match(/\d{1,3}(?:,\d{3})*|\d+/g);
      if (numbers && numbers.length > 0) {
        const parsed = Number(numbers[numbers.length - 1].replace(/,/g, ''));
        if (Number.isFinite(parsed) && parsed > 0) {
          return parsed;
        }
      }
    }
  }

  const bodyText = await page.locator('body').innerText();
  const patterns = [
    /(?:Documents?|Results?)\s*\(?\s*(\d{1,3}(?:,\d{3})*|\d+)\s*\)?/gi,
    /of\s+(\d{1,3}(?:,\d{3})*|\d+)\s+(?:Documents?|Results?)/gi,
  ];

  for (const pattern of patterns) {
    const matches = [...bodyText.matchAll(pattern)];
    if (matches.length > 0) {
      for (const m of matches) {
        const parsed = Number(m[1].replace(/,/g, ''));
        if (Number.isFinite(parsed) && parsed > 0) {
          return parsed;
        }
      }
    }
  }

  throw new Error(
    'Could not automatically determine total document count. Update selectors in findTotalDocumentCount().',
  );
}

async function findTotalDocumentCountWithRecovery(page, { timeoutMs, headless }) {
  // If the search string is invalid / not submitted / lands on an unexpected page,
  // the total-count detection will fail. In headed mode, pause to let the user
  // correct the query or navigate to results, then retry when they resume.
  //
  // In headless mode, pausing is not possible, so we fail fast with a clear message.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      return await findTotalDocumentCount(page);
    } catch (err) {
      const msg = err && err.message ? err.message : String(err);
      if (headless) {
        throw new Error(
          `Failed to detect total document count in headless mode. Ensure the search ran and results are open. Details: ${msg}`,
        );
      }

      console.warn(`Total document count not detected yet: ${msg}`);
      console.log(
        'Pausing so you can fix the search/query and navigate to the results list. When you click Play/Resume, I will retry total-count detection.',
      );
      await page.pause();

      // Small buffer after resume to let the UI settle.
      await page.waitForTimeout(500);

      // Avoid hanging forever in cases where the page is still loading.
      try {
        await page.waitForLoadState('domcontentloaded', { timeout: timeoutMs });
      } catch {
        // ignore
      }
    }
  }
}

async function openFast5kDialog(page, timeoutMs) {
  const exportBtn = page.getByRole('button', { name: 'Export', exact: true });
  await exportBtn.waitFor({ timeout: timeoutMs });
  await exportBtn.click();

  const fastOption = page.getByRole('menuitem', { name: 'Fast' });
  await fastOption.waitFor({ timeout: timeoutMs });
  await fastOption.click();
}

async function acceptCookiesIfPresent(page, timeoutMs) {
  // Startup wait so the cookie modal has time to render.
  await page.waitForTimeout(5000);

  const acceptAll = page.getByRole('button', { name: /Accept all/i });
  try {
    await acceptAll.waitFor({ timeout: Math.min(timeoutMs, 20_000) });
    await acceptAll.click();
    await page.waitForTimeout(500);
    console.log('Accepted cookies.');
  } catch {
    // Not always shown (or already accepted).
  }
}

async function signInIfPossible(page, { email, password }, timeoutMs) {
  // If already signed in, there may be no sign-in button.
  const signInBtn = page.getByRole('button', { name: /Sign\s*In/i });
  if ((await signInBtn.count()) === 0) return;

  await signInBtn.first().waitFor({ timeout: timeoutMs });
  await signInBtn.first().click();

  // Some tenants show a nested "Sign In" link in a menu.
  const signInLink = page.locator('a').filter({ hasText: /Sign\s*In/i }).first();
  if ((await signInLink.count()) > 0) {
    await signInLink.click();
  }

  const emailInput = page.getByRole('textbox', { name: /Email address/i });
  await emailInput.waitFor({ timeout: timeoutMs });
  await emailInput.click();
  await emailInput.fill(email);

  let passwordInput = page.getByRole('textbox', { name: /Password/i });
  if ((await passwordInput.count()) === 0) {
    passwordInput = page.locator('input[type="password"]').first();
  } else {
    passwordInput = passwordInput.first();
  }

  await passwordInput.waitFor({ timeout: timeoutMs });
  await passwordInput.fill(password);

  const signInConfirm = page.getByRole('button', { name: /^Sign in$/i });
  if ((await signInConfirm.count()) > 0) {
    await signInConfirm.click();
  } else {
    // Fallback if button text differs slightly.
    await page.getByRole('button', { name: /Sign in/i }).first().click();
  }

  // Give auth redirect a moment; different tenants vary.
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000);
}

function readSearchStringFromFile(searchFilePath) {
  try {
    if (!fs.existsSync(searchFilePath)) return null;

    // Read + normalize common formatter damage in-place.
    // VS Code SQL formatters sometimes rewrite year ranges like:
    //   FPY=2020-2024  ->  FPY = 2020 -2024
    // which breaks WoS parsing (space before '-').
    const originalRaw = fs.readFileSync(searchFilePath, 'utf8').replace(/^\uFEFF/, '');

    // 1) Fix year ranges where a formatter inserts spaces around '-'
    const fixedYearRanges = originalRaw.replace(
      /\b(FPY|PY)\b(\s*=\s*)(\d{4})\s*-\s*(\d{4})\b/g,
      '$1$2$3-$4',
    );

    // 2) Fix wildcard tokens where a formatter inserts a space before '*'
    //    e.g. "energ *" -> "energ*". (We only remove the literal " *" sequence.)
    const fixedWildcards = fixedYearRanges.replace(/ \*/g, '*');

    if (fixedWildcards !== originalRaw) {
      fs.writeFileSync(searchFilePath, fixedWildcards, 'utf8');
      // Re-read to ensure we use exactly what is on disk.
      const didYear = fixedYearRanges !== originalRaw;
      const didStar = fixedWildcards !== fixedYearRanges;
      const fixes = [didYear ? "year ranges" : null, didStar ? "wildcards" : null].filter(Boolean).join(' + ');
      console.log(`Normalized ${fixes} in ${path.basename(searchFilePath)}.`);
    }

    const raw = fs.readFileSync(searchFilePath, 'utf8').replace(/^\uFEFF/, '');
    const trimmed = raw.trim();
    if (!trimmed) return null;

    // WOS query parser ignores whitespace; collapsing keeps the query robust when filled into a textbox.
    return trimmed.replace(/\s+/g, ' ').trim();
  } catch (err) {
    console.warn(`Warning: failed reading search string from ${searchFilePath}: ${err.message}`);
    return null;
  }
}

async function runAdvancedSearch(page, searchString, timeoutMs) {
  const advancedSearchUrl = 'https://www.webofscience.com/wos/woscc/advanced-search';
  const queryBox = page.getByRole('textbox', { name: /Query Preview/i });

  try {
    await queryBox.waitFor({ timeout: Math.min(timeoutMs, 10_000) });
  } catch {
    // If login redirected elsewhere, navigate back to Advanced Search.
    await page.goto(advancedSearchUrl, { waitUntil: 'domcontentloaded' });
    await queryBox.waitFor({ timeout: timeoutMs });
  }

  await queryBox.click();
  await queryBox.fill(searchString);

  // The recorder captured a tokenized URL; in practice the UI needs a submit action.
  // Try Enter first, then fall back to a Search button if no navigation happens.
  const beforeUrl = page.url();
  try {
    await queryBox.press('Enter');
  } catch {
    // ignore
  }

  await page.waitForTimeout(750);

  if (page.url() === beforeUrl) {
    const searchBtn = page.getByRole('button', { name: /^Search$/i });
    if ((await searchBtn.count()) > 0) {
      await searchBtn.first().click();
    } else {
      const searchBtnLoose = page.getByRole('button', { name: /Search/i });
      if ((await searchBtnLoose.count()) > 0) {
        await searchBtnLoose.first().click();
      }
    }
  }

  // Best-effort wait for results page elements. (Do not throw here; pause/manual steps can still fix it.)
  try {
    await page.getByRole('button', { name: 'Export', exact: true }).waitFor({ timeout: timeoutMs });
    return true;
  } catch {
    return page.url() !== beforeUrl;
  }
}

async function setRangeAndFileName(page, { start, end, baseName, index, timeoutMs }) {
  const startInput = page.getByRole('spinbutton', { name: 'Input starting record range' });
  const endInput = page.getByRole('spinbutton', { name: 'Input ending record range. A' });

  await startInput.waitFor({ timeout: timeoutMs });
  await endInput.waitFor({ timeout: timeoutMs });

  await startInput.click();
  await startInput.fill(String(start));
  await startInput.press('Tab');
  await endInput.fill(String(end));

  // Note: some WoS tenants don't provide a filename input for Fast 5K export.
  // We handle deterministic naming by choosing our own local filename in saveAs().
  void baseName;
  void index;
}

function buildOutputFilename({ suggested, baseName, index, totalBatches }) {
  const parsed = path.parse(suggested);
  const ext = (parsed.ext || '.txt').toLowerCase();
  if (ext !== '.txt') {
    throw new Error(`Invalid file type: expected .txt, got ${suggested}`);
  }

  const seq = String(index + 1);
  const effectiveBase = (baseName && String(baseName).trim()) ? String(baseName).trim() : parsed.name;

  // Ensure we don't accidentally create path segments.
  const safeBase = path.basename(effectiveBase);
  return `${safeBase} ${seq}${ext}`;
}

async function exportSingleBatch(page, { timeoutMs, index, totalBatches, baseName }) {
  const exportConfirm = page.locator('#exportButton');

  await exportConfirm.waitFor({ timeout: timeoutMs });

  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: timeoutMs }),
    exportConfirm.click(),
  ]);

  // Suggested names are often the same (e.g., savedrecs.txt) and can include browser
  // suffixes like "(1)". We save to a deterministic sequential filename instead.
  const suggested = path.basename(download.suggestedFilename());
  const outputName = buildOutputFilename({
    suggested,
    baseName,
    index,
    totalBatches,
  });

  const savePath = path.resolve('./downloads', outputName);
  await download.saveAs(savePath);
  
  // Validate file size (max 100MB)
  const stats = fs.statSync(savePath);
  const maxSize = 100 * 1024 * 1024;
  if (stats.size > maxSize) {
    fs.unlinkSync(savePath);
    throw new Error(`File too large: ${stats.size} bytes (max ${maxSize})`);
  }
  
  return outputName;
}

async function main() {
  const args = parseArgs(process.argv);

  // Load environment variables from a local .env in this script folder.
  // (Ignored by repo .gitignore.)
  loadDotEnv(path.resolve(__dirname, '.env'));

  fs.mkdirSync(path.resolve('./downloads'), { recursive: true });

  const browser = await chromium.launch({
    headless: args.headless,
    slowMo: args.slowMo,
  });

  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();

  await page.goto('https://www.webofscience.com/wos/woscc/advanced-search', {
    waitUntil: 'domcontentloaded',
  });

  await acceptCookiesIfPresent(page, args.timeoutMs);

  const email = process.env.WOS_EMAIL;
  const password = process.env.WOS_PWD;
  if (args.autoLogin && email && password) {
    console.log('Attempting automated Sign In using WOS_EMAIL/WOS_PWD from .env...');
    await signInIfPossible(page, { email, password }, args.timeoutMs);
  } else {
    console.log('Automated login not configured (set WOS_EMAIL and WOS_PWD in .env), continuing with manual login.');
  }

  if (args.autoSearch) {
    const searchFilePath = path.isAbsolute(args.searchFile)
      ? args.searchFile
      : path.resolve(__dirname, args.searchFile);
    const searchString = readSearchStringFromFile(searchFilePath);
    if (searchString) {
      console.log(`Applying SEARCH_STRING from ${path.basename(searchFilePath)} and submitting search...`);
      const ok = await runAdvancedSearch(page, searchString, args.timeoutMs);
      if (!ok) {
        console.warn('Warning: search submit may not have completed. You can complete it manually in the paused browser.');
      }
    } else {
      console.log(`No search string found at ${path.basename(searchFilePath)}; skipping auto-search.`);
    }
  }

  if (args.pauseAfterLogin) {
    console.log('Pausing (requested) — verify login/results page, then resume.');
    await page.pause();
  }

  const total = await findTotalDocumentCountWithRecovery(page, {
    timeoutMs: args.timeoutMs,
    headless: args.headless,
  });
  console.log(`Detected total documents: ${total}`);

  const ranges = batchRanges(total, args.batchSize);
  console.log(`Preparing ${ranges.length} Fast 5K batch export(s):`, ranges);

  await page.evaluate(() => {
    const el = document.querySelector('body');
    if (!el) return;
    // no-op to keep lint happy in plain Node execution contexts
  });

  for (let i = 0; i < ranges.length; i += 1) {
    const range = ranges[i];
    console.log(`\n[${i + 1}/${ranges.length}] Exporting ${range.start}-${range.end}`);

    await openFast5kDialog(page, args.timeoutMs);
    await setRangeAndFileName(page, {
      ...range,
      baseName: args.baseName,
      index: i,
      timeoutMs: args.timeoutMs,
    });

    const fileName = await exportSingleBatch(page, {
      timeoutMs: args.timeoutMs,
      index: i,
      totalBatches: ranges.length,
      baseName: args.baseName,
    });
    console.log(`Downloaded: ${fileName}`);
  }

  console.log('\nAll Fast 5K exports completed successfully.');
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
