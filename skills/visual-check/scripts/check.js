#!/usr/bin/env node
'use strict';
/*
 * check.js — screenshots one screen of the app so a change can be checked by eye.
 *
 * Usage (from the project root): node check.js <path> [options]
 * See ../SKILL.md. Besides the PNG, it reports JavaScript errors, console errors and
 * HTTP responses >= 400: a screen can "look" fine and still be broken.
 */
const fs = require('fs');
const path = require('path');
const { DEFAULT_CONFIG, fail, loadConfig, openBrowser, prepare, textOf, mutatingPattern, slug, cacheDir } = require('./common');
const { settle } = require('./walkthrough');

const HELP = `Usage: node check.js <path> [options]
  --config FILE        project config (default ${DEFAULT_CONFIG})
  --click "SEL1|SEL2"  click in order (panels, tabs, dropdowns, dialogs)
  --type "SEL|text"    type into a field (filters, search boxes)
  --wait MS|SEL        extra wait, or wait until a selector is visible
  --text SEL           print the element's text
  --exists SEL         report whether the element exists and is visible
  --redact SEL         also blur these elements (separated by |)
  --full               full page
  --mobile             phone viewport (390x844)
  --width N --height N viewport (default 1440x900)
  --html               also save the rendered HTML
  --mock FILE          mocked JSON responses {"**/api/x": {...}}
  --allow-change       allow clicking buttons that change data (only with authorization)
  --out NAME           output file name`;

function parseArgs(argv) {
    const a = { _: [] };
    const withValue = ['config', 'click', 'type', 'wait', 'text', 'exists', 'redact', 'width', 'height', 'mock', 'out'];
    for (let i = 0; i < argv.length; i++) {
        const k = argv[i].replace(/^--/, '');
        if (!argv[i].startsWith('--')) a._.push(argv[i]);
        else if (withValue.includes(k)) a[k] = argv[++i];
        else a[k] = true;
    }
    return a;
}

async function main() {
    const o = parseArgs(process.argv.slice(2));
    if (!o._.length || o.help) { console.log(HELP); process.exit(o._.length ? 0 : 1); }
    const route = o._[0];
    const config = loadConfig(o.config || DEFAULT_CONFIG);

    const width = o.mobile ? 390 : parseInt(o.width || 1440, 10);
    const height = o.mobile ? 844 : parseInt(o.height || 900, 10);
    const { browser, page } = await openBrowser({ width, height, scale: 1, config });

    const problems = [];
    page.on('pageerror', (e) => problems.push('JS: ' + e.message.split('\n')[0]));
    page.on('console', (m) => { if (m.type() === 'error') problems.push('console: ' + m.text().slice(0, 200)); });
    page.on('response', (r) => { if (r.status() >= 400) problems.push(`HTTP ${r.status()}: ${r.url().slice(0, 160)}`); });

    if (o.mock) {
        for (const [pattern, body] of Object.entries(JSON.parse(fs.readFileSync(o.mock, 'utf8')))) {
            await page.route(pattern, (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) }));
        }
    }

    try {
        const resp = await page.goto(config.baseUrl + route, { waitUntil: 'networkidle' });
        await settle(page, o.wait && /^\d+$/.test(o.wait) ? parseInt(o.wait, 10) : o.wait);

        const mutating = mutatingPattern(config);
        for (const sel of (o.click ? o.click.split('|') : [])) {
            const label = await textOf(page, sel.trim());
            if (mutating.test(label) && !o['allow-change']) {
                fail(`"${label}" looks like it changes data; it is not clicked without --allow-change (and explicit authorization)`);
            }
            await page.locator(sel.trim()).filter({ visible: true }).first().click();
            await settle(page);
        }
        if (o.type) {
            const [sel, text] = o.type.split('|');
            const field = page.locator(sel.trim()).filter({ visible: true }).first();
            await field.fill('');
            await field.pressSequentially(text, { delay: 20 });
            await settle(page);
        }
        if (o.text) {
            const el = page.locator(o.text).first();
            console.log((await el.count()) ? 'text: ' + (await el.innerText()) : `text: "${o.text}" not found`);
        }
        if (o.exists) {
            const el = page.locator(o.exists).first();
            const n = await el.count();
            console.log(`exists=${n > 0} visible=${n > 0 && (await el.isVisible())}`);
        }

        await prepare(page, config, { redact: o.redact ? o.redact.split('|') : [] });
        const dir = cacheDir('screenshots', slug(config.app));
        fs.mkdirSync(dir, { recursive: true });
        const base = o.out || [route.replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-|-$/g, '') || 'root', o.mobile ? 'mobile' : ''].filter(Boolean).join('-');
        const png = path.join(dir, base + '.png');
        if (o.full) {
            // Grow the viewport instead of fullPage: stitching duplicates position:fixed elements.
            await page.setViewportSize({ width, height: await page.evaluate(() => document.documentElement.scrollHeight) });
            await page.waitForTimeout(300);
        }
        await page.screenshot({ path: png });
        console.log('screenshot: ' + png);
        if (o.html) {
            fs.writeFileSync(path.join(dir, base + '.html'), await page.content());
            console.log('html: ' + path.join(dir, base + '.html'));
        }

        const bodyText = await page.evaluate(() => document.body ? document.body.innerText.trim().length : 0);
        if (resp && resp.status() === 200 && bodyText === 0) problems.push('blank page with HTTP 200: check the server log for a render error');
        const pathOf = (u) => new URL(u).pathname.replace(/\/+$/, '');
        if (pathOf(page.url()) !== pathOf(config.baseUrl + route)) {
            problems.push(`redirected to ${page.url()}: the page may need sign-in or another precondition (ask the user how to handle it)`);
        }
        console.log(problems.length ? 'problems:\n  - ' + [...new Set(problems)].join('\n  - ') : 'problems: none');
    } finally {
        await browser.close();
    }
}

main().catch((e) => fail(e.stack || e.message));
