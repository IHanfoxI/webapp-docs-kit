# Capture pitfalls

Things that make screenshots of real web apps come out wrong, and how to avoid them.

## Selectors

- Prefer stable attributes: `[data-testid=...]`, `[name=...]`, `[aria-label=...]`,
  roles and visible text (`button:has-text('Export')`). Avoid generated class
  names (`.css-1x2y3z`) and long positional chains.
- Do not use `:has-text()` on large containers (panels, tables). It may match
  text inside a different panel. Narrow it to the header or title element.
- Custom dropdowns usually render their options in a popup attached at the end
  of `body`. Click the trigger first, then the option inside that popup.
- To crop a dialog, use the dialog element itself (`[role=dialog]`, `.modal.show`).
- Run `check.js <path> --html` and search the saved HTML before guessing selectors.

## Screens that come out wrong

- **Blank page with HTTP 200:** the server failed while rendering. The reason
  is in the server log. It is a bug in the app: tell the user.
- **Half-transparent dialog:** a fade-in animation had not finished. Use
  `"wait": 800` or `"wait": "[role=dialog]"` on the step (`--wait` in `check.js`).
- **Empty chart or spinner:** data loads after `networkidle`. Wait for the
  rendered element (`"wait": "canvas"`, `"wait": ".chart svg"`).
- **Cut-off table text:** fixed-height scrollable tables force `nowrap`. In the
  manual, crop the screenshot or use `"fullPage": true`.
- **Duplicated fixed headers in full-page shots:** the scripts grow the viewport
  instead of using Playwright's `fullPage` stitching, which avoids this.
- **Cookie banners, chat widgets, dev toolbars:** add them to `hide` in the config.

## Single-page apps

- Use `"noNavigation": true` in `login` when signing in does not reload the page.
- If the login cannot be scripted (SSO, MFA), seed the session with
  `check.js --session session.json` (`{"key": "token", "value": "...", "storage": "local"}`)
  using a **test** session, or mock the API with `--mock`.

## JSF / PrimeFaces

- JSF prefixes ids with the form id. Use `[id$='field']` (ends with), not `#field`.
- Collapsible panels: click `.ui-panel-titlebar-icon`, not the whole title bar.
- `p:selectOneMenu`: click `.ui-selectonemenu-trigger`, then
  `li.ui-selectonemenu-item[data-label='Option']` inside the panel appended to `body`.
- Dialogs: crop with `.ui-dialog:visible` or `[id$='dlgName']`; they use
  `showEffect="fade"`, so add a wait.
- The scripts already wait for the PrimeFaces and jQuery AJAX queues to drain.

## Rules

- Typing into filters and clicking tabs, panels and menus is safe. Never click
  anything that confirms, signs, cancels, sends, pays or deletes without the
  user's explicit authorization.
- Open every screenshot. A command that exits cleanly does not prove the image is right.
