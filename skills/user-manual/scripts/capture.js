#!/usr/bin/env node
'use strict';
/*
 * capture.js — runs a walkthrough and saves the manual screenshots.
 *
 * Usage: node capture.js docs/webapp-docs.json docs/manuals/<name>/walkthrough.json
 *
 * Saves one PNG for every step with "screenshot": "<name>", taken after the step runs,
 * in <walkthrough folder>/screenshots/<name>.png. "mark" draws the red box,
 * "crop": "<selector>" crops the image to that element (dialogs, panels) and
 * "fullPage": true captures the whole page.
 */
const fs = require('fs');
const path = require('path');
const SHARED = path.join(__dirname, '..', '..', 'visual-check', 'scripts');
const { fail, loadConfig, loadWalkthrough, openBrowser } = require(path.join(SHARED, 'common'));
const { run } = require(path.join(SHARED, 'walkthrough'));

async function main() {
    const [configFile, walkFile] = process.argv.slice(2);
    if (!walkFile) fail('usage: node capture.js <webapp-docs.json> <walkthrough.json>');
    const config = loadConfig(configFile);
    const walk = loadWalkthrough(walkFile);
    const outDir = path.join(walk._dir, 'screenshots');
    fs.mkdirSync(outDir, { recursive: true });

    const m = config.manual || {};
    const width = m.width || 1440, height = m.height || 900;
    const { browser, page } = await openBrowser({ width, height, scale: m.scale || 2, config });
    const done = [];
    try {
        await run(page, config, walk, {
            before: async () => {},
            after: async (step, info) => {
                if (!step.screenshot) return;
                if (step.mark) {
                    await page.evaluate((marks) => {
                        for (const r of marks) {
                            const d = document.createElement('div');
                            d.className = '__wdk-mark';
                            Object.assign(d.style, {
                                position: 'fixed', left: (r.x - 5) + 'px', top: (r.y - 5) + 'px',
                                width: (r.w + 10) + 'px', height: (r.h + 10) + 'px',
                                border: '3px solid #E5252A', borderRadius: '6px', zIndex: 2147483647, pointerEvents: 'none',
                            });
                            document.documentElement.appendChild(d);
                        }
                    }, info.marks);
                }
                const file = path.join(outDir, step.screenshot + '.png');
                if (step.crop) {
                    const b = await page.locator(step.crop).filter({ visible: true }).first().boundingBox();
                    if (!b) fail(`crop: selector not visible ${step.crop}`);
                    const pad = 8;
                    const x = Math.max(0, b.x - pad), y = Math.max(0, b.y - pad);
                    await page.screenshot({ path: file, clip: { x, y, width: Math.min(width - x, b.width + 2 * pad), height: Math.min(height - y, b.height + 2 * pad) } });
                } else if (step.fullPage) {
                    // Grow the viewport instead of fullPage: fullPage stitching duplicates position:fixed elements.
                    const total = await page.evaluate(() => document.documentElement.scrollHeight);
                    await page.setViewportSize({ width, height: total });
                    await page.waitForTimeout(300);
                    await page.screenshot({ path: file });
                    await page.setViewportSize({ width, height });
                } else {
                    await page.screenshot({ path: file });
                }
                await page.evaluate(() => document.querySelectorAll('.__wdk-mark').forEach((n) => n.remove()));
                done.push(file);
                console.log('screenshot: ' + file);
            },
        });
    } finally {
        await browser.close();
    }
    if (!done.length) console.log('Note: no step in the walkthrough has "screenshot".');
}

main().catch((e) => fail(e.stack || e.message));
