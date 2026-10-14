'use strict';
/*
 * common.js — project config and browser. Used by check.js,
 * user-manual/scripts/capture.js and video-tutorial/scripts/record.js.
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const { chromium } = require('playwright-core');

const KIT = 'webapp-docs-kit';
const DEFAULT_CONFIG = 'docs/webapp-docs.json';

function fail(msg) {
    console.error('Error: ' + msg);
    process.exit(1);
}

function slug(s) {
    return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// Working files live outside every repository: ~/.cache/webapp-docs-kit/...
function cacheDir(...parts) {
    return path.join(process.env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache'), KIT, ...parts);
}

function expandHome(p) {
    return p.startsWith('~') ? path.join(os.homedir(), p.slice(1)) : p;
}

// The project's docs/webapp-docs.json.
function loadConfig(file) {
    if (!fs.existsSync(file)) fail(`${file} does not exist`);
    const config = JSON.parse(fs.readFileSync(file, 'utf8'));
    config._dir = path.dirname(path.resolve(file));
    for (const k of ['app', 'baseUrl']) {
        if (!config[k]) fail(`missing "${k}" in ${file}`);
    }
    return config;
}

// A walkthrough is identified by its folder: docs/manuals/<name>/walkthrough.json.
function loadWalkthrough(file) {
    if (!fs.existsSync(file)) fail(`${file} does not exist`);
    const walk = JSON.parse(fs.readFileSync(file, 'utf8'));
    walk._dir = path.dirname(path.resolve(file));
    walk._name = slug(path.basename(walk._dir)) || 'walkthrough';
    return walk;
}

async function openBrowser({ width, height, scale, config }) {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        ignoreHTTPSErrors: !!config.ignoreHttpsErrors,
        viewport: { width, height },
        deviceScaleFactor: scale,
        locale: config.locale || 'en-US',
    });
    return { browser, context, page: await context.newPage() };
}

// Hides dev chrome and blurs personal data before every screenshot.
async function prepare(page, config, step = {}) {
    const hide = [].concat(config.hide || []);
    if (hide.length) {
        await page.addStyleTag({ content: hide.join(',') + '{display:none !important}' }).catch(() => {});
    }
    const redact = [].concat(config.redact || [], step.redact || []);
    for (const sel of redact) {
        await page.locator(sel).evaluateAll((ns) => ns.forEach((n) => { n.style.filter = 'blur(6px)'; })).catch(() => {});
    }
}

// Rectangle (CSS px of the viewport) of the first visible match.
async function rect(page, selector) {
    const loc = page.locator(selector).filter({ visible: true }).first();
    await loc.waitFor({ state: 'visible', timeout: 15000 }).catch(() => fail(`selector not visible: ${selector}`));
    await loc.scrollIntoViewIfNeeded();
    const b = await loc.boundingBox();
    return { x: b.x, y: b.y, w: b.width, h: b.height };
}

// Buttons that change data. They can be shown with "simulate": true, but not clicked
// without "allowChange": true on the step (and the user's explicit authorization).
// Projects in other languages add their own words with "protectedLabels" in the config.
const MUTATING = ['delete', 'remove', 'save', 'submit', 'send', 'sign', 'create', 'approve', 'reject',
    'confirm', 'publish', 'accept', 'register', 'upload', 'import', 'pay', 'purchase', 'buy', 'checkout',
    'order', 'transfer', 'archive', 'cancel subscription', 'deactivate', 'revoke', 'reset'];

function mutatingPattern(config) {
    const words = MUTATING.concat(config.protectedLabels || []);
    return new RegExp(words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'i');
}

async function textOf(page, selector) {
    return page.locator(selector).filter({ visible: true }).first()
        .evaluate((n) => (n.innerText || n.value || n.getAttribute('title') || n.getAttribute('aria-label') || '').trim())
        .catch(() => '');
}

module.exports = {
    KIT, DEFAULT_CONFIG, fail, slug, cacheDir, expandHome, loadConfig, loadWalkthrough,
    openBrowser, prepare, rect, textOf, mutatingPattern,
};
