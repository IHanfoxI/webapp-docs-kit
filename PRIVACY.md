# Privacy policy

*Last updated: 2026-10-13*

webapp-docs-kit is a set of open-source agent skills that run entirely on your
computer. The author does not operate any server for it and receives no data
from it.

## What is collected

Nothing. The skills have no telemetry, analytics, accounts or remote logging.

## What the skills access on your machine

- **Your web app**, through a local headless browser, at the `baseUrl` you
  configure in `docs/webapp-docs.json`. Screenshots can contain anything that
  app shows; selectors listed in `redact` are blurred before each capture.
- **No credentials.** The skills never read, ask for, type or store
  passwords, tokens or cookies.
- **Files** written to your project (`docs/`) and to `~/.cache/webapp-docs-kit/`
  and your video output folder.

## Network access

- The browser opens only your configured `baseUrl` and whatever that app loads.
- On first use, `npm` downloads `playwright-core` from the npm registry and
  Playwright downloads Chromium from its CDN. Those services have their own
  privacy policies.
- Your AI agent (Claude Code, Codex, etc.) sees the screenshots and text it
  reads while running the skills, under that agent provider's own terms.

## Children

The skills are developer tools and are not directed at children under 18.

## Contact

Questions: open an issue at <https://github.com/IHanfoxI/webapp-docs-kit/issues>.
