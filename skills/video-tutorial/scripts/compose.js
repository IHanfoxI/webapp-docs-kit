#!/usr/bin/env node
'use strict';
/*
 * compose.js — builds the 1920x1080 MP4 from the timeline.json written by record.js.
 *
 * Usage: node compose.js <timeline.json> <output.mp4> [--music track.mp3] [--volume 0.25] [--preview]
 *
 * Frame by frame and deterministic: a compositing page draws every frame (zoomed
 * screenshot, red box, cursor, caption, cover/scene/closing cards) and ffmpeg encodes
 * it at 30 fps, H.264 yuv420p. Also writes <output>.srt with the captions and, with
 * --music, <output>-music.mp4 with that track mixed in. --preview only renders contact
 * sheets (one frame per step) to review before the full render.
 */
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');
const { pathToFileURL } = require('url');
const SHARED = path.join(__dirname, '..', '..', 'visual-check', 'scripts');
const { chromium } = require(path.join(SHARED, 'node_modules', 'playwright-core'));
const { fail } = require(path.join(SHARED, 'common'));

const FPS = 30;
const W = 1920, H = 1080;
const CAPTION_H = 230;               // bottom band reserved for the caption
const ZOOM_MAX = 2.2;                // the source is at device scale 2: up to ~2x stays sharp
const RED = '#E5252A';
const LABELS = { cover: 'Video walkthrough', step: 'Step', of: 'of', end: 'End of walkthrough' };

// ── Timing (seconds) ─────────────────────────────────────────────────────────
const T = { cover: 4, scene: 2.4, end: 4.5, move: 1.0, mark: 0.5, pulse: 0.45, fade: 0.45, after: 0.7 };
const reading = (text) => Math.min(8, Math.max(2.6, text.length / 15));

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const mix = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

function camera(step) {
    const full = { s: 1, x: 0, y: 0 };
    if (step.action === 'go' && !step.marks.length) return full;
    if (step.zoom === false) return full;
    const rs = [...step.marks, ...(step.target ? [step.target] : [])];
    if (!rs.length) return full;
    const x0 = Math.min(...rs.map((r) => r.x)), y0 = Math.min(...rs.map((r) => r.y));
    const x1 = Math.max(...rs.map((r) => r.x + r.w)), y1 = Math.max(...rs.map((r) => r.y + r.h));
    let s = typeof step.zoom === 'number' ? step.zoom
        : Math.min(0.6 * W / (x1 - x0 + 80), 0.55 * (H - CAPTION_H) / (y1 - y0 + 80));
    s = clamp(s, 1, ZOOM_MAX);
    if (s < 1.15) s = 1;
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    return {
        s,
        x: clamp(cx - W / (2 * s), 0, W - W / s),
        y: clamp(cy - (H - CAPTION_H) / (2 * s), 0, H - H / s),
    };
}

const toScreen = (cam, p) => ({ x: (p.x - cam.x) * cam.s, y: (p.y - cam.y) * cam.s });
const mixCam = (a, b, t) => ({ s: mix(a.s, b.s, t), x: mix(a.x, b.x, t), y: mix(a.y, b.y, t) });

// ── Timeline: segments with a duration and a state(t) ───────────────────────
function build(tl) {
    const seg = [];
    const subs = [];
    let clock = 0;
    const add = (d, state, sub) => {
        if (sub) subs.push({ from: clock, to: clock + d, text: sub });
        seg.push({ d, state });
        clock += d;
    };
    const card = (kind, data, d) => add(d, (t) => ({
        card: { kind, ...data, alpha: Math.min(1, t / 0.4, (d - t) / 0.4) },
    }));

    card('cover', { app: tl.app, role: tl.role, title: tl.title }, T.cover);

    let cam = { s: 1, x: 0, y: 0 };
    let img = null;
    let cursor = { x: W / 2, y: H / 2 };
    let scene = null;
    const total = tl.steps.length;
    for (const p of tl.steps) {
        if (p.scene && p.scene !== scene) {
            scene = p.scene;
            card('scene', { text: scene, app: tl.app, role: tl.role }, T.scene);
        }
        const camNew = camera(p);
        const camPrev = cam, imgPrev = img || p.before, cursorPrev = cursor;
        const dest = p.target ? { x: p.target.x + Math.min(p.target.w / 2, 60), y: p.target.y + p.target.h / 2 } : null;
        const withCursor = p.action === 'click' || p.action === 'type';
        // The caption moves to the top if the target, once zoomed, would sit under the bottom band.
        const bottom = p.marks.concat(p.target ? [p.target] : [])
            .every((r) => toScreen(camNew, { x: 0, y: r.y + r.h }).y < H - CAPTION_H - 10);
        const stepScene = scene;
        const caption = (alpha) => ({ text: p.text, scene: stepScene, n: p.index, total, alpha, top: !bottom });
        const marks = (c, alpha, grow) => p.marks.map((r) => {
            const a = toScreen(c, r);
            return { x: a.x, y: a.y, w: r.w * c.s, h: r.h * c.s, alpha, grow };
        });
        const ptr = (c, pos, alpha, pulse) => (pos ? { ...toScreen(c, pos), alpha, pulse } : null);

        // 1. Camera and cursor move to the target, cross-fading to the new screenshot.
        add(T.move, (t) => {
            const k = ease(t / T.move);
            const c = mixCam(camPrev, camNew, k);
            const pos = dest ? { x: mix(cursorPrev.x, dest.x, k), y: mix(cursorPrev.y, dest.y, k) } : null;
            return {
                a: imgPrev, b: p.before, blend: Math.min(1, t / T.fade), cam: c,
                cursor: withCursor ? ptr(c, pos, 1, -1) : null,
                sub: caption(clamp((t - 0.5) / 0.4, 0, 1)),
            };
        });
        // 2. The red box appears. 3. Reading pause.
        const read = p.pause || reading(p.text);
        add(T.mark + read, (t) => ({
            a: p.before, cam: camNew, marks: marks(camNew, Math.min(1, t / T.mark), 1 - Math.min(1, t / T.mark)),
            cursor: withCursor ? ptr(camNew, dest, 1, -1) : null, sub: caption(1),
        }), p.text);
        // 4. Action.
        if (p.action === 'click') {
            add(T.pulse, (t) => ({
                a: p.before, cam: camNew, marks: marks(camNew, 1, 0),
                cursor: ptr(camNew, dest, 1, t / T.pulse), sub: caption(1),
            }));
            add(T.fade + T.after, (t) => ({
                a: p.before, b: p.after, blend: Math.min(1, t / T.fade), cam: camNew,
                marks: marks(camNew, Math.max(0, 1 - t / T.fade), 0),
                cursor: ptr(camNew, dest, 1, -1), sub: caption(1),
            }));
        } else if (p.action === 'type') {
            const frames = p.typing.length ? p.typing : [p.after];
            const d = clamp(frames.length * 0.28, 0.6, 2.2);
            add(d, (t) => ({
                a: frames[Math.min(frames.length - 1, Math.floor(t / d * frames.length))], cam: camNew,
                marks: marks(camNew, 1, 0), cursor: ptr(camNew, dest, 1, -1), sub: caption(1),
            }));
            add(T.after, () => ({
                a: p.after, cam: camNew, marks: marks(camNew, 1, 0), cursor: ptr(camNew, dest, 1, -1), sub: caption(1),
            }));
        }
        // Caption fades out before the next step.
        add(0.3, (t) => ({
            a: p.after, cam: camNew, cursor: withCursor ? ptr(camNew, dest, 1, -1) : null, sub: caption(1 - t / 0.3),
        }));
        cam = camNew; img = p.after;
        if (dest && withCursor) cursor = dest;
    }
    // Back to the full screen, then the closing card.
    const last = img, camEnd = cam;
    add(1.0, (t) => ({ a: last, cam: mixCam(camEnd, { s: 1, x: 0, y: 0 }, ease(t)) }));
    card('end', { app: tl.app, role: tl.role, support: tl.support }, T.end);
    return { seg, subs, duration: clock };
}

// ── Compositing page ────────────────────────────────────────────────────────
function compositingHtml({ logo, primary, accent, labels }) {
    return `<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0}
html,body{width:${W}px;height:${H}px;overflow:hidden;background:#0f172a;font-family:Inter,'Segoe UI',Roboto,Carlito,Calibri,'Helvetica Neue',Arial,sans-serif}
#cam{position:absolute;left:0;top:0;width:${W}px;height:${H}px;transform-origin:0 0}
#cam img{position:absolute;left:0;top:0;width:${W}px;height:${H}px}
.mark{position:absolute;border:5px solid ${RED};border-radius:10px;box-shadow:0 0 0 5px rgba(229,37,42,.22),0 0 24px rgba(229,37,42,.35)}
#cursor{position:absolute;width:40px;height:40px;margin:-4px 0 0 -6px;filter:drop-shadow(0 3px 4px rgba(0,0,0,.45))}
#pulse{position:absolute;border:4px solid ${RED};border-radius:50%}
#sub{position:absolute;left:50%;transform:translateX(-50%);min-width:900px;max-width:1560px;background:rgba(15,23,42,.92);color:#fff;
  border-left:10px solid ${accent};border-radius:14px;padding:26px 38px 30px;box-shadow:0 10px 40px rgba(0,0,0,.35)}
#sub .meta{font-size:24px;color:#a5b4cb;letter-spacing:.5px;margin-bottom:8px;font-weight:700;text-transform:uppercase}
#sub .txt{font-size:40px;line-height:1.28;font-weight:600}
#sub b{color:#FCD34D}
#card{position:absolute;inset:0;background:linear-gradient(135deg,${primary} 0%,color-mix(in srgb,${primary} 70%,${accent}) 100%);color:#fff;
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
#card img{max-width:420px;max-height:220px;margin-bottom:46px}
#card .k{font-size:30px;letter-spacing:4px;text-transform:uppercase;color:rgba(255,255,255,.75);font-weight:700}
#card .t{font-size:84px;font-weight:700;margin:18px 120px;line-height:1.1}
#card .r{font-size:44px;color:#FCD34D;font-weight:600}
#card .s{font-size:30px;color:rgba(255,255,255,.85);margin-top:30px}
#card .bar{width:140px;height:8px;background:${accent};border-radius:4px;margin:30px 0}
</style></head><body>
<div id="cam"><img id="a"><img id="b"></div>
<div id="marks"></div>
<div id="pulse" style="display:none"></div>
<svg id="cursor" viewBox="0 0 24 24" style="display:none"><path d="M3 2 L3 19 L7.5 14.8 L10.6 21.5 L13.6 20.2 L10.6 13.6 L16.8 13.6 Z" fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg>
<div id="sub" style="display:none"><div class="meta"></div><div class="txt"></div></div>
<div id="card" style="display:none"></div>
<script>
const LOGO=${JSON.stringify(logo)};
const L=${JSON.stringify(labels)};
const $=(id)=>document.getElementById(id);
const esc=(s)=>String(s||'').replace(/[&<>]/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const bold=(s)=>esc(s).replace(/\\*\\*(.+?)\\*\\*/g,'<b>$1</b>');
const logo=()=>LOGO?'<img src="'+LOGO+'">':'';
async function put(img,src){
  if(!src){img.style.display='none';return}
  img.style.display='block';
  if(img.dataset.src!==src){img.dataset.src=src;img.src=src;await img.decode()}
}
window.draw=async(e)=>{
  const t=e.card;
  $('card').style.display=t?'flex':'none';
  if(t){
    $('card').style.opacity=t.alpha;
    const html = t.kind==='cover'
      ? logo()+'<div class="k">'+esc(L.cover)+'</div><div class="t">'+esc(t.app)+'</div><div class="r">'+esc(t.role)+'</div>'+(t.title?'<div class="s">'+esc(t.title)+'</div>':'')
      : t.kind==='scene'
      ? '<div class="k">'+esc(t.app)+' · '+esc(t.role)+'</div><div class="bar"></div><div class="t">'+esc(t.text)+'</div>'
      : logo()+'<div class="t">'+esc(L.end)+'</div><div class="r">'+esc(t.app)+' · '+esc(t.role)+'</div>'+(t.support?'<div class="s">'+esc(t.support)+'</div>':'');
    if($('card').dataset.html!==html){$('card').dataset.html=html;$('card').innerHTML=html;await Promise.all([...$('card').querySelectorAll('img')].map(i=>i.decode().catch(()=>{})))}
    if(t.alpha>=1){$('cam').style.display='none';$('sub').style.display='none';$('cursor').style.display='none';$('marks').innerHTML='';return}
  }
  $('cam').style.display='block';
  await put($('a'),e.a); await put($('b'),e.b);
  $('b').style.opacity=e.b?e.blend:0;
  const c=e.cam||{s:1,x:0,y:0};
  $('cam').style.transform='translate('+(-c.x*c.s)+'px,'+(-c.y*c.s)+'px) scale('+c.s+')';
  $('marks').innerHTML=(e.marks||[]).map(m=>{const p=10+14*m.grow;return '<div class="mark" style="left:'+(m.x-p)+'px;top:'+(m.y-p)+'px;width:'+(m.w+2*p)+'px;height:'+(m.h+2*p)+'px;opacity:'+m.alpha+'"></div>'}).join('');
  const k=e.cursor;
  $('cursor').style.display=k?'block':'none';
  if(k){$('cursor').style.left=k.x+'px';$('cursor').style.top=k.y+'px';$('cursor').style.opacity=k.alpha}
  const pul=k&&k.pulse>=0;
  $('pulse').style.display=pul?'block':'none';
  if(pul){const r=12+40*k.pulse;Object.assign($('pulse').style,{left:(k.x-r)+'px',top:(k.y-r)+'px',width:2*r+'px',height:2*r+'px',opacity:1-k.pulse})}
  const s=e.sub;
  $('sub').style.display=s&&s.alpha>0?'block':'none';
  if(s){
    $('sub').style.opacity=s.alpha;
    $('sub').style.top=s.top?'40px':'auto';$('sub').style.bottom=s.top?'auto':'40px';
    $('sub').querySelector('.meta').textContent=L.step+' '+s.n+' '+L.of+' '+s.total+(s.scene?' · '+s.scene:'');
    $('sub').querySelector('.txt').innerHTML=bold(s.text);
  }
};
</script></body></html>`;
}

function srt(subs) {
    const hms = (s) => {
        const ms = Math.round(s * 1000);
        const p = (n, l = 2) => String(n).padStart(l, '0');
        return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`;
    };
    return subs.map((s, i) => `${i + 1}\n${hms(s.from)} --> ${hms(s.to)}\n${s.text.replace(/\*\*/g, '')}\n`).join('\n');
}

function dataUri(file) {
    const ext = path.extname(file).toLowerCase();
    const mime = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp' }[ext];
    if (!mime) fail(`unsupported logo format: ${file} (use PNG, JPG, SVG or WebP)`);
    return `data:${mime};base64,` + fs.readFileSync(file).toString('base64');
}

async function main() {
    const args = process.argv.slice(2);
    const [timelineFile, output] = args;
    if (!output) fail('usage: node compose.js <timeline.json> <output.mp4> [--music track.mp3] [--volume 0.25] [--preview]');
    const opt = (k) => { const i = args.indexOf(k); return i > 0 ? args[i + 1] : null; };
    const preview = args.includes('--preview');
    const tl = JSON.parse(fs.readFileSync(timelineFile, 'utf8'));
    // file:// URLs that also work with Windows paths (C:\...).
    const url = (r) => (r ? pathToFileURL(r).href : r);
    for (const p of tl.steps) Object.assign(p, { before: url(p.before), after: url(p.after), typing: p.typing.map(url) });
    const { seg, subs, duration } = build(tl);
    fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });

    const page_ = compositingHtml({
        logo: tl.logo ? dataUri(tl.logo) : null,
        primary: tl.primaryColor || '#1E293B',
        accent: tl.accentColor || '#2563EB',
        labels: { ...LABELS, ...(tl.labels || {}) },
    });
    const compositing = path.join(path.dirname(path.resolve(timelineFile)), 'compositing.html');
    fs.writeFileSync(compositing, page_);

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
    await page.goto(pathToFileURL(compositing).href);

    const stateAt = (time) => {
        let t = time;
        for (const s of seg) {
            if (t < s.d) return s.state(t);
            t -= s.d;
        }
        const u = seg[seg.length - 1];
        return u.state(u.d);
    };

    if (preview) {
        // One frame in the middle of every segment with a reading pause, plus a contact sheet.
        const dir = output.replace(/\.mp4$/, '') + '-preview';
        fs.mkdirSync(dir, { recursive: true });
        let n = 0;
        for (const s of seg) {
            if (s.d >= 2) {
                await page.evaluate((e) => window.draw(e), s.state(s.d * 0.6));
                await page.screenshot({ path: path.join(dir, `frame-${String(++n).padStart(3, '0')}.png`) });
            }
        }
        await browser.close();
        // Numbered sequence rather than a glob: ffmpeg has no -pattern_type glob on Windows.
        execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', path.join(dir, 'frame-%03d.png'),
            '-vf', 'scale=480:-1,tile=4x' + Math.ceil(n / 4), '-frames:v', '1', path.join(dir, 'sheet.png')]);
        console.log(`preview: ${n} frames in ${dir} (sheet.png). Estimated duration ${duration.toFixed(1)} s`);
        return;
    }

    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS), '-movflags', '+faststart', output],
        { stdio: ['pipe', 'inherit', 'inherit'] });
    const finished = new Promise((ok, ko) => ff.on('close', (c) => (c === 0 ? ok() : ko(new Error('ffmpeg exited with code ' + c)))));
    const frames = Math.ceil(duration * FPS);
    let prev = null, buf = null;
    for (let f = 0; f < frames; f++) {
        const e = stateAt(f / FPS);
        const key = JSON.stringify(e);
        if (key !== prev) {
            await page.evaluate((x) => window.draw(x), e);
            buf = await page.screenshot({ type: 'jpeg', quality: 92 });
            prev = key;
        }
        if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
        if (f % (FPS * 10) === 0) process.stdout.write(`\r${Math.round(100 * f / frames)}%`);
    }
    ff.stdin.end();
    await finished;
    await browser.close();
    fs.writeFileSync(output.replace(/\.mp4$/, '.srt'), srt(subs));
    console.log(`\rvideo: ${output} (${duration.toFixed(1)} s)`);

    const music = opt('--music');
    if (music) {
        if (!fs.existsSync(music)) fail(`music track not found: ${music}`);
        const vol = opt('--volume') || '0.25';
        const withMusic = output.replace(/\.mp4$/, '-music.mp4');
        const end = Math.max(0, duration - 2).toFixed(2);
        execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', output, '-stream_loop', '-1', '-i', music, '-filter_complex',
            `[1:a]atrim=0:${duration.toFixed(2)},afade=t=in:d=1,afade=t=out:st=${end}:d=2,volume=${vol}[a]`,
            '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', withMusic]);
        console.log('video with music: ' + withMusic);
    }
}

main().catch((e) => fail(e.stack || e.message));
