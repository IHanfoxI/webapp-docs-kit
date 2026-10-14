#!/usr/bin/env node
'use strict';
/*
 * record.js — runs a role's walkthrough on a Full HD "monitor" and saves every state.
 *
 * Usage: node record.js docs/webapp-docs.json docs/manuals/<role>/walkthrough.json [--work DIR]
 *
 * Not a real-time recording: it takes a screenshot before and after every step (and a few
 * while typing) at 1920x1080 with device scale 2 (3840x2160 real pixels). That keeps the
 * zooms in compose.js sharp and keeps server wait times out of the video.
 * Writes <work>/timeline.json with everything compose.js needs.
 */
const fs = require('fs');
const path = require('path');
const SHARED = path.join(__dirname, '..', '..', 'visual-check', 'scripts');
const { fail, loadConfig, loadWalkthrough, openBrowser, expandHome, slug, cacheDir } = require(path.join(SHARED, 'common'));
const { run, ACTIONS } = require(path.join(SHARED, 'walkthrough'));

const WIDTH = 1920, HEIGHT = 1080, SCALE = 2;

async function main() {
    const args = process.argv.slice(2);
    const [configFile, walkFile] = args;
    if (!walkFile) fail('usage: node record.js <webapp-docs.json> <walkthrough.json> [--work DIR]');
    const config = loadConfig(configFile);
    const walk = loadWalkthrough(walkFile, config);
    const i = args.indexOf('--work');
    const work = i > 0 ? expandHome(args[i + 1]) : cacheDir('video', slug(config.app), walk.role);
    fs.rmSync(work, { recursive: true, force: true });
    fs.mkdirSync(work, { recursive: true });

    const { browser, page } = await openBrowser({ width: WIDTH, height: HEIGHT, scale: SCALE, config });
    const steps = [];
    const shot = async (name) => {
        const file = path.join(work, name + '.png');
        await page.screenshot({ path: file });
        return file;
    };
    const num = (info) => String(info.index).padStart(3, '0');
    try {
        await run(page, config, walk, {
            before: async (step, info) => {
                steps.push({
                    index: info.index,
                    scene: info.scene.title || '',
                    text: step.text,
                    action: ACTIONS.find((k) => step[k] !== undefined),
                    zoom: step.zoom,
                    pause: step.pause,
                    target: info.target,
                    marks: info.marks,
                    before: await shot(`s${num(info)}-before`),
                    typing: [],
                });
                process.stdout.write(`step ${info.index}: ${step.text.slice(0, 70)}\n`);
            },
            typing: async (step, info) => {
                const s = steps[steps.length - 1];
                s.typing.push(await shot(`s${num(info)}-t${s.typing.length + 1}`));
            },
            after: async (step, info) => {
                steps[steps.length - 1].after = await shot(`s${num(info)}-after`);
            },
        });
    } finally {
        await browser.close();
    }
    const v = config.video || {};
    const logo = v.logo ? path.resolve(config._dir, expandHome(v.logo)) : null;
    if (logo && !fs.existsSync(logo)) fail(`video.logo not found: ${logo}`);
    const timeline = {
        app: config.app,
        role: config.roles[walk.role].name || walk.role,
        title: walk.title || '',
        support: config.support || '',
        logo,
        primaryColor: v.primaryColor || null,
        accentColor: v.accentColor || null,
        labels: v.labels || {},
        width: WIDTH, height: HEIGHT,
        steps,
    };
    fs.writeFileSync(path.join(work, 'timeline.json'), JSON.stringify(timeline, null, 2));
    console.log('timeline: ' + path.join(work, 'timeline.json'));
}

main().catch((e) => fail(e.stack || e.message));
