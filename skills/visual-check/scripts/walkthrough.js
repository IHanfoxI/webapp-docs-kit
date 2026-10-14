'use strict';
/*
 * walkthrough.js — runs a walkthrough (docs/manuals/<role>/walkthrough.json) against the real app.
 * The same walkthrough feeds the manual screenshots and the video recording:
 * each consumer gets hooks before and after every step.
 */
const { fail, login, prepare, rect, textOf, mutatingPattern } = require('./common');

const ACTIONS = ['go', 'click', 'type', 'highlight'];

async function settle(page, wait) {
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    // AJAX queues that networkidle does not always cover (jQuery, PrimeFaces/JSF).
    await page.waitForFunction(() => (!window.jQuery || !window.jQuery.active) &&
        (!window.PrimeFaces || !PrimeFaces.ajax || PrimeFaces.ajax.Queue.isEmpty()),
        null, { timeout: 15000 }).catch(() => {});
    if (typeof wait === 'number') await page.waitForTimeout(wait);
    else if (typeof wait === 'string') await page.waitForSelector(wait, { state: 'visible', timeout: 20000 });
    await page.waitForTimeout(350);
}

function validate(walk) {
    const steps = walk.scenes.flatMap((s) => s.steps);
    if (!steps.length || !steps[0].go) fail('the first step of a walkthrough must be "go"');
    for (const s of steps) {
        const actions = ACTIONS.filter((k) => s[k] !== undefined);
        if (actions.length !== 1) fail(`each step needs exactly one action (${ACTIONS.join('/')}): ${JSON.stringify(s)}`);
        if (!s.text) fail(`step without "text": ${JSON.stringify(s)}`);
    }
}

/**
 * hooks.before(step, info) / hooks.after(step, info) / hooks.typing(step, info, fraction)
 * info = { scene, index, target: rect|null, marks: [rect] }
 */
async function run(page, config, walk, hooks) {
    validate(walk);
    const mutating = mutatingPattern(config);
    let loggedIn = false;
    let index = 0;
    for (const scene of walk.scenes) {
        for (const step of scene.steps) {
            index++;
            const info = { scene, index, target: null, marks: [] };
            if (step.go !== undefined) {
                if (!step.public && !loggedIn) {
                    await login(page, config, walk.role);   // off camera
                    loggedIn = true;
                }
                await page.goto(config.baseUrl + step.go, { waitUntil: 'networkidle' });
                await settle(page, step.wait);
                await prepare(page, config, step);
                for (const s of [].concat(step.mark || [])) info.marks.push(await rect(page, s));
                await hooks.before(step, info);
                await hooks.after(step, info);
                continue;
            }
            const sel = step.click || step.type || step.highlight;
            info.target = await rect(page, sel);
            for (const s of [].concat(step.mark || sel)) info.marks.push(s === sel ? info.target : await rect(page, s));
            await prepare(page, config, step);
            await hooks.before(step, info);

            if (step.click && !step.simulate) {
                const label = await textOf(page, sel);
                if (mutating.test(label) && !step.allowChange) {
                    fail(`step ${index} clicks "${label}", which looks like it changes data. ` +
                         'Use "simulate": true, or "allowChange": true only with explicit authorization and in a test environment.');
                }
                await page.locator(sel).filter({ visible: true }).first().click();
                await settle(page, step.wait);
            } else if (step.type) {
                const field = page.locator(sel).filter({ visible: true }).first();
                const value = String(step.value || '');
                await field.fill('');
                // Typed in chunks so the video shows the text appearing.
                const chunks = Math.min(6, Math.max(1, Math.ceil(value.length / 4)));
                for (let c = 1; c <= chunks; c++) {
                    await field.fill(value.slice(0, Math.round(value.length * c / chunks)));
                    if (hooks.typing) await hooks.typing(step, info, c / chunks);
                }
                await field.dispatchEvent('change').catch(() => {});
                if (step.pressEnter) await field.press('Enter');
                await settle(page, step.wait);
            } else if (step.wait) {
                await settle(page, step.wait);
            }
            await prepare(page, config, step);
            await hooks.after(step, info);
        }
    }
}

module.exports = { run, settle, ACTIONS };
