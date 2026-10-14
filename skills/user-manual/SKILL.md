---
name: user-manual
description: Writes end-user manuals for a web app as PDF and DOCX, one per role, with real screenshots taken with Playwright and a clean Word template (cover, header, footer, table of contents). Use when asked for "/user-manual", a user manual, a user guide, how-to documentation or training material for the end users of a web app.
argument-hint: "[role | all]"
---

# User manual

Produces **one manual per role** with real screenshots of the app and the
template in `template/manual-template.docx` (cover, header, footer and table of
contents). The result follows `references/manual-style.md`.

In this guide `$H` is this skill's `scripts/` folder and `$V` is
`../visual-check/scripts`. `$V` holds the config loader, the login and the
walkthrough runner shared by the three webapp-docs-kit skills.

## Before you start

1. If `$V/node_modules` does not exist, run `cd $V && npm install`. The browser
   is installed once with `node $V/node_modules/playwright-core/cli.js install chromium`.
2. Read the project's `README.md` and `CLAUDE.md`/`AGENTS.md`. Find the roles in
   the auth configuration (route guards, middleware, security annotations,
   `web.xml`, policies) or the navigation menu. Find each role's screens and how
   the app is started.
3. **Ask the user** what you cannot work out from the code:
   - Which environment to capture: local, dev or staging. **Never use production.**
   - Which roles to document. Default: every role that has a test user.
   - The names of the environment variables with each role's test credentials.
     The user keeps them in a local file outside the repository,
     `~/.config/webapp-docs-kit/<project>.env` (or `.ps1` on Windows), and loads
     it before starting the agent, or in Claude Code with
     `! source ~/.config/webapp-docs-kit/<project>.env` (this also works on
     Windows, where Claude Code runs Git Bash). **Never write credentials to a
     repository file or to the chat.**
   - The organization shown on the cover and the support contact.
   - The language of the manual, if it is not English (see "Other languages").

## Steps

1. **Project config.** Create or update `docs/webapp-docs.json` following
   `../visual-check/references/configuration.md`. It is the same config
   `/visual-check` uses. If it already exists, use it.
2. **Walkthrough per role.** Write `docs/manuals/<role>/walkthrough.json`:
   scenes and steps covering what that role can do. Add `"screenshot"` to the
   steps that get a figure in the manual. `/video-tutorial` uses the same file.
   The format is in `references/walkthrough-format.md`. To find selectors, run
   `node $V/check.js <path> --role <role> --html` and look at the screenshot
   before writing long walkthroughs. Selector tips are in
   `../visual-check/references/capture-pitfalls.md`.
3. **Screenshots.**
   ```bash
   cd <project>
   node $H/capture.js docs/webapp-docs.json docs/manuals/<role>/walkthrough.json
   ```
   **Open every PNG.** Check that no screen came out blank, that personal data
   is blurred (`redact`), that no dev chrome shows, and that each crop shows
   what the text describes. If something is off, fix the walkthrough and rerun.
4. **Text.** Write `docs/manuals/<role>/manual.md` following
   `references/manual-style.md` and `references/markdown-format.md`. Describe
   only what the role sees and can do, confirmed in the screenshots and in the
   code. Do not invent features.
5. **Build.**
   ```bash
   cd docs/manuals
   python3 $H/build_manual.py <role>/manual.md <role>/manual-<app>-<role>.docx
   python3 $H/to_pdf.py <role>/manual-<app>-<role>.docx \
       --title "User manual — <App> — <Role>" --author "<Organization>"
   ```
   On Windows use `python` instead of `python3`. `to_pdf.py` recomputes the
   table of contents and writes the `.pdf` next to the `.docx`. It uses
   LibreOffice when installed (and relaunches itself with LibreOffice's Python
   if needed) or Microsoft Word on Windows.
6. **Mandatory visual review.** Render the PDF to images with
   `pdftoppm -r 50 -png manual.pdf <temp folder>/pg` and open them. Check that
   the table of contents has page numbers, that no figure is cut off and that no
   table overflows. Do not call the manual done without looking at it.
7. Repeat steps 2 to 6 for every requested role.

## Rules

- **One manual per role.** If two roles share screens, each manual repeats
  them. Readers only open their own.
- **Screenshots never change data.** `capture.js` refuses to click Save,
  Delete, Submit, Send, Sign and similar buttons. Use `"simulate": true` on
  those steps: the button is highlighted but not clicked. Use
  `"allowChange": true` only with the user's explicit authorization for that
  step, and only in a test environment.
- Use test users, never real ones. Blur every column with personal data.
- If a screen looks different from what you expected, tell the user. It may be
  a bug in the app. Do not hide it in the manual.

## Other languages

Write `manual.md` in the target language and set `title`, `preface_title`,
`contents_title` and `figure_label` in its front matter (see
`references/markdown-format.md`). Add the language's destructive button labels
to `protectedLabels` in the config.

## Custom template

The default template is neutral (no logos). To brand it, either regenerate it
with other colors (`python3 $H/build_template.py out.docx --primary 0F766E --accent F59E0B [--letter]`)
or open it in Word/LibreOffice, add a logo, change fonts and colors, keep the
`{{...}}` markers, and pass it with `--template my-template.docx`.
`build_manual.py` stops and says what is missing if the template is unusable.

## Delivery

Leave in `docs/manuals/<role>/` the `walkthrough.json`, `manual.md`,
`screenshots/`, the `.docx` and the `.pdf`. At the end, report each PDF's path,
its page count, and any screen that could not be captured.
