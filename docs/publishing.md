# Publishing and listing (maintainers)

This repository is already a **plugin marketplace** for Claude Code and for
Codex, so anyone can install it from GitHub without any submission. Listing it
in the official directories is optional and goes through a review.

## Files involved

| File | Read by | Purpose |
|---|---|---|
| `.claude-plugin/plugin.json` | Claude Code | Plugin manifest (name, version, author, license). Skills are discovered from `skills/`. |
| `.claude-plugin/marketplace.json` | Claude Code | Makes the repo a marketplace with one plugin whose `source` is the repo root (`"./"`). |
| `plugin.json` | Codex / ChatGPT | Portable plugin manifest with the `extensions.com.openai.interface` listing data. Skills are discovered from `skills/`. |
| `.agents/plugins/marketplace.json` | Codex | Repo marketplace with the plugin at `"./"`, `policy` and `category` (both required). |
| `skills/*/SKILL.md` | every Agent Skills client | The skills themselves (`name` + `description` frontmatter). |

Keep `name` identical in every manifest (`webapp-docs-kit`). Never rename a
published plugin: existing installs are recorded under the old name.

## Releasing a new version

1. Bump `version` in `.claude-plugin/plugin.json` **and** `plugin.json`, and
   add an entry to `CHANGELOG.md`. Claude Code does not update users whose
   installed `version` equals the published one.
2. Validate (Claude Code ≥ 2.1): `claude plugin validate --strict .`
3. Test a local install before pushing:
   `claude plugin marketplace add ./` then `claude plugin install webapp-docs-kit@webapp-docs-kit`.
   For Codex: `codex plugin marketplace add ./` (or the GitHub shorthand after pushing).
4. Commit, tag (`git tag v1.1.0`) and push.

Users update with `claude plugin update webapp-docs-kit@webapp-docs-kit`,
`codex plugin marketplace upgrade`, `npx skills update` or `git pull` (installer links).

## Anthropic's directory (claude.ai / Claude Code)

- Directory: <https://claude.ai/directory>. Submissions go through the developer
  portal at <https://claude.ai/directory/manage>; the walkthrough is at
  <https://claude.com/docs/plugins/submit>.
- You need a paid claude.ai plan (Pro/Max from your own account; on Team or
  Enterprise an Owner submits).
- Before submitting run `claude plugin validate --strict .` and the
  [pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist).
  Check the [component support table](https://claude.com/docs/plugins/platform-support):
  these skills run local scripts (Node, Playwright, ffmpeg) against a running
  app, so they are useful in **Claude Code**; on claude.ai or Cowork they
  cannot reach a local app.
- The official `claude-plugins-official` marketplace does not take
  submissions through the portal.
- Once listed, users who add it on claude.ai also get it in Claude Code as `webapp-docs-kit@synced`.

## OpenAI plugin directory (ChatGPT / Codex)

- Public plugins are submitted once to a directory shared by ChatGPT and Codex:
  <https://platform.openai.com/plugins> → *Upload new or existing plugin*.
  Process: <https://developers.openai.com/plugins/deploy/submission>.
- Skills-only plugins (like this one) are accepted: no MCP server, test cases
  or demo recording needed, but the automated skill scans must pass.
- You need a verified individual or business identity in your OpenAI
  organization settings, and an owner (or the *Apps Management Write* permission).
- Upload a ZIP of the plugin. Exclude `node_modules/`, `examples/`, and
  anything with secrets: `git archive -o webapp-docs-kit.zip HEAD -- plugin.json skills README.md LICENSE`.
- Listing data: display name and subtitle ≤ 30 characters, description ≤ 4,000,
  and a square logo plus composer icon (≥ 48×48 px, PNG/JPEG/WebP/SVG, ≤ 5 MiB).
  Add `composerIcon` and `logo` to `extensions.com.openai.interface` in `plugin.json` when you have them.

## Community catalogs

- `npx skills add IHanfoxI/webapp-docs-kit` works as soon as the repo is public
  (the [skills CLI](https://github.com/vercel-labs/skills) discovers `skills/*/SKILL.md`).
  Installs are counted on <https://skills.sh>.
- Add the GitHub topics `agent-skills`, `claude-code`, `codex`, `playwright` so
  people can find the repository.
