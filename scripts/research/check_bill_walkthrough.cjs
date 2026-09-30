/* Browser acceptance for the offline, deterministic meeting walkthrough. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.argv[2] || 'playwright');
const url = process.argv[3] || 'http://127.0.0.1:8771/bill-pressure-walkthrough.html';
const out = path.resolve(process.argv[4] || 'packs/oil-gas/outputs/bill-meeting-browser');
if (new URL(url).hostname !== '127.0.0.1') throw Error('Only the local walkthrough may be tested');
if (fs.existsSync(out)) throw Error('Use a fresh result directory');
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const errors = [], requests = [], checks = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1080 } });
    page.on('pageerror', e => errors.push(e.message));
    await page.route('**/*', route => {
      requests.push(route.request().url());
      return new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort();
    });
    await page.goto(url);
    assert.equal(await page.locator('#result-value').textContent(), '40.6 psia'); checks.push('gauge conversion');
    await page.screenshot({ path: path.join(out, 'desktop.png'), fullPage: true });
    await page.locator('[data-case=vacuum]').click();
    assert.equal(await page.locator('#result-value').textContent(), '7.1 psia'); checks.push('vacuum sign');
    await page.locator('#atmosphere').fill('');
    assert.equal(await page.locator('#result-value').textContent(), 'Missing evidence'); checks.push('unknown atmosphere');
    await page.locator('[data-case=missing]').click();
    assert.equal(await page.locator('#result-value').textContent(), 'Ask before calculating'); checks.push('unknown pressure basis');
    await page.locator('[data-case=safety]').click();
    await page.locator('#atmosphere').fill('14.7');
    assert.equal(await page.locator('#result-value').textContent(), 'No operating approval'); checks.push('conversion cannot approve operation');
    await page.locator('[data-case=convert]').click();
    await page.locator('#reading').fill('-50');
    assert.equal(await page.locator('#result-value').textContent(), 'Check the inputs'); checks.push('negative absolute rejected');
    await page.locator('#basis').selectOption('absolute');
    await page.locator('#reading').fill('0');
    assert.equal(await page.locator('#result-value').textContent(), '0 psia'); checks.push('absolute zero is not missing');
    await page.locator('#tab-review').focus(); await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#tab-evidence').getAttribute('aria-selected'), 'true'); checks.push('keyboard tabs');
    await page.screenshot({ path: path.join(out, 'evidence.png'), fullPage: true });
    await page.locator('#tab-teach').click();
    assert.match(await page.locator('#teach').textContent(), /Not trained/);
    assert.match(await page.locator('#teach').textContent(), /Not scored/); checks.push('no fabricated training results');
    await page.locator('#tab-priority').click();
    await page.locator('#task').fill('Synthetic meeting note: compare document revisions');
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#export').click();
    const download = await downloadPromise;
    await download.saveAs(path.join(out, 'synthetic-notes.json'));
    const notes = JSON.parse(fs.readFileSync(path.join(out, 'synthetic-notes.json'), 'utf8'));
    assert.equal(notes.answers.task, 'Synthetic meeting note: compare document revisions');
    assert.equal(notes.training_approved, false);
    assert.equal(notes.status, 'draft_needs_participant_review'); checks.push('draft export preserves notes without permission');
    for (const tab of ['review', 'evidence', 'teach', 'priority']) {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.locator('#tab-' + tab).click();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    }
    checks.push('all four mobile panels fit');
    await page.locator('#tab-review').click(); await page.locator('[data-case=convert]').click();
    await page.screenshot({ path: path.join(out, 'mobile.png'), fullPage: true });
    assert.deepEqual(errors, []); checks.push('no browser errors');
    assert.equal(requests.some(x => new URL(x).hostname !== '127.0.0.1'), false); checks.push('no external requests');
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify({ status: 'passed', checks, count: checks.length,
      scope: 'Rule-based local walkthrough only; no model calls or training', errors }, null, 2)+'\n');
    console.log(JSON.stringify({ status: 'passed', checks: checks.length, errors }));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
