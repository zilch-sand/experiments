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

function parseArgs(argv) {
  const args = {
    headless: false,
    batchSize: 5000,
    baseName: '',
    timeoutMs: 30_000,
    slowMo: 100,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--headless') {
      args.headless = argv[i + 1] !== 'false';
      i += 1;
    } else if (arg === '--batch-size') {
      args.batchSize = Number(argv[i + 1]);
      i += 1;
    } else if (arg === '--base-name') {
      args.baseName = argv[i + 1] || '';
      i += 1;
    } else if (arg === '--timeout-ms') {
      args.timeoutMs = Number(argv[i + 1]);
      i += 1;
    } else if (arg === '--slow-mo') {
      args.slowMo = Number(argv[i + 1]);
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

async function openFast5kDialog(page, timeoutMs) {
  const exportBtn = page.getByRole('button', { name: /export/i }).first();
  await exportBtn.waitFor({ timeout: timeoutMs });
  await exportBtn.click();

  const fast5kOption = page.getByRole('menuitem', { name: /fast\s*5k/i }).first();
  if ((await fast5kOption.count()) > 0) {
    await fast5kOption.click();
    return;
  }

  const fast5kButton = page.getByRole('button', { name: /fast\s*5k/i }).first();
  if ((await fast5kButton.count()) > 0) {
    await fast5kButton.click();
    return;
  }

  const fast5kText = page.getByText(/fast\s*5k/i).first();
  await fast5kText.click({ timeout: timeoutMs });
}

async function setRangeAndFileName(page, { start, end, baseName, index, timeoutMs }) {
  const startInput = page
    .locator('input[name*=start i], input[aria-label*=start i], input[id*=start i]')
    .first();
  const endInput = page
    .locator('input[name*=end i], input[aria-label*=end i], input[id*=end i]')
    .first();

  await startInput.waitFor({ timeout: timeoutMs });
  await endInput.waitFor({ timeout: timeoutMs });

  await startInput.fill(String(start));
  await endInput.fill(String(end));

  if (baseName) {
    const fileNameInput = page
      .locator('input[name*=file i], input[aria-label*=file i], input[id*=file i], input[placeholder*=file i]')
      .first();

    if ((await fileNameInput.count()) > 0) {
      const seq = String(index + 1);
      await fileNameInput.fill(`${baseName} ${seq}`);
    }
  }
}

async function exportSingleBatch(page, timeoutMs) {
  const exportConfirm = page
    .getByRole('button', { name: /^(export|download|submit)$/i })
    .first();

  await exportConfirm.waitFor({ timeout: timeoutMs });

  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: timeoutMs }),
    exportConfirm.click(),
  ]);

  const suggested = download.suggestedFilename();
  await download.saveAs(`./downloads/${suggested}`);
  return suggested;
}

async function main() {
  const args = parseArgs(process.argv);

  fs.mkdirSync(path.resolve('./downloads'), { recursive: true });

  const browser = await chromium.launch({
    headless: args.headless,
    slowMo: args.slowMo,
  });

  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();

  await page.goto('https://www.webofscience.com/wos/woscc/basic-search', {
    waitUntil: 'domcontentloaded',
  });

  console.log('Please log in and open your search results page.');
  await page.pause();

  const total = await findTotalDocumentCount(page);
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

    const fileName = await exportSingleBatch(page, args.timeoutMs);
    console.log(`Downloaded: ${fileName}`);

    await page.waitForTimeout(1500);
  }

  console.log('\nAll Fast 5K exports completed successfully.');
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
