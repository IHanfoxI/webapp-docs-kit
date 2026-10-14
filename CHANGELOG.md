# Changelog

## 2.0.0 — 2026-10-13

The kit no longer makes assumptions about the app it documents.

- **Breaking:** removed sign-in and credentials (`login`, `credentialsEnv`,
  `--role`, `--no-login`, `--session`, `"public"`). If screens are behind a login
  or any other precondition, the agent stops and asks the user how to handle it.
- **Breaking:** removed roles. `roles` in the config and `role` in walkthroughs are
  gone; each manual or video is a named walkthrough (`docs/manuals/<name>/`).
  The manual front matter uses an optional `subtitle` instead of `role`.
- `check.js` reports unexpected redirects (for example to a login page).
- The default Word template is cached as `manual-template-v2.docx`.

## 1.0.1 — 2026-10-13

Prepares the plugin for Anthropic's plugin directory.

- The default Word template is generated on first use (`build_template.py`, cached in
  `~/.cache/webapp-docs-kit/`) instead of being shipped as a binary `.docx`.
- Example PDF/DOCX outputs moved from the repository to the release downloads.
- `npx skills` commands pinned to an exact version.
- README: new "What it runs, downloads, sends and stores" section.

## 1.0.0 — 2026-10-13

First public release.

- `visual-check`: role-aware screenshots with JavaScript, console, HTTP and blank-page diagnostics.
- `user-manual`: one PDF/DOCX manual per role on a neutral, regenerable Word template;
  PDF export through LibreOffice or Microsoft Word.
- `video-tutorial`: one 1920×1080 MP4 per role with zoom, highlight box, cursor and captions,
  `.srt` subtitles and optional music, logo and colors.
- Install as a Claude Code or Codex plugin marketplace, with `npx skills`, Gemini CLI,
  or the `install.sh` / `install.ps1` scripts.
- TodoMVC example.
