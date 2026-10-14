---
name: visual-check
description: Visually verifies UI changes in a web app. Takes Playwright screenshots of the affected screens while signed in with the right role, looks at them, and reports JavaScript errors, console errors, failed HTTP responses and blank pages. Use when asked for "/visual-check", after finishing a change to anything the user sees (views, styles, components, messages), or to see how a screen looks for a given role. Does not produce manuals or videos.
argument-hint: "[path or description of the change]"
---

# Visual check

A UI change is not done until someone **looks** at the screen. A successful
build, a deploy and an HTTP `200` prove nothing about what the user will see. A
collapsed panel, an icon that fails to load, a half-transparent dialog or
personal data left unblurred only show up in the screenshot.

`$V` is this skill's `scripts/` folder. The `user-manual` and `video-tutorial`
skills of webapp-docs-kit reuse these scripts.

## Before you start

1. If `$V/node_modules` does not exist, run `cd $V && npm install` and
   `node node_modules/playwright-core/cli.js install chromium`.
2. Look for `docs/webapp-docs.json` in the project. If it is missing, create it
   following `references/configuration.md`. Take the base URL, the login form
   and the roles from the project's `README.md`, `CLAUDE.md`/`AGENTS.md`, route
   definitions, auth configuration and navigation menu. Ask the user only for
   what you cannot work out:
   - The environment: local, dev or staging. **Never use production.**
   - The names of the environment variables that hold each role's **test**
     credentials. The user loads them before starting the agent, or in Claude
     Code with `! source ~/.config/webapp-docs-kit/<project>.env` (this also
     works on Windows, where Claude Code runs Git Bash). **Never write
     credentials to a repository file or to the chat.**
3. The change must be running in that environment. If it is not, follow the
   project's own instructions to build and start or deploy it.

## Steps

1. **Pick what to check.** Take the views touched by the change (`git diff`)
   and, for each one, the roles that see it. If the change depends on state (an
   open panel, an applied filter, a dialog), reproduce it with `--click` and `--type`.
2. **Screenshot** from the project root:
   ```bash
   node $V/check.js <path> --role <role> [options]
   ```
   | Option | Purpose |
   |---|---|
   | `--click "SEL1\|SEL2"` | Open panels, tabs, dropdowns and dialogs, in order |
   | `--type "SEL\|text"` | Type into filters and search boxes |
   | `--wait MS\|SEL` | Slow screens or animated dialogs |
   | `--full` | Full page |
   | `--mobile` | Phone viewport (390×844), when the view must be responsive |
   | `--exists SEL` / `--text SEL` | Check an element without looking at the image. Useful to tune selectors |
   | `--html` | Save the rendered HTML to look for selectors |
   | `--no-login` | Public pages |
   | `--redact SEL` | Blur more personal data on top of the config's `redact` list |
   | `--session FILE` / `--mock FILE` | SPAs whose login cannot be scripted, or screens that need fake API data |

   The screenshot is saved in `~/.cache/webapp-docs-kit/screenshots/<app>/`, outside the repository.
3. **Open the image with your file-reading tool. Do not skip this step.** Check
   that the change looks as requested and that nothing around it broke:
   alignment, clipped text, overlaps, icons, colors and empty states.
4. **Read the `problems:` section of the output.** Report JavaScript errors,
   console errors, HTTP responses ≥ 400, blank pages and redirects to the
   login page. A new error on a screen that looks fine is still a defect.
5. If something is wrong, fix it, redeploy and take the screenshot again.
   Compare it with the previous one.

## Rules

- **Read-only.** `--click` and `--type` are for filtering, navigating and
  opening panels. `check.js` refuses to click Save, Delete, Submit, Send, Sign
  and similar buttons. Use `--allow-change` only when the user explicitly
  authorizes that specific case, and only in a test environment.
- Use the **real role** that sees the screen. An admin may see things the end user cannot.
- `--text` prints unblurred data to the terminal. Do not copy it into documents or commits.
- Known pitfalls (prefixed ids, animated dialogs, charts that render late,
  JSF/PrimeFaces, SPAs) are in `references/capture-pitfalls.md`.

## Report

For each screen checked, give the path, the role, whether it looks right or
what is wrong, the problems detected, and the screenshot path. Do not say
"verified" unless you opened the image.
