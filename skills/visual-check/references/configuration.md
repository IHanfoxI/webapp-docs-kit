# Project configuration

`docs/webapp-docs.json`, one per project. Used by `/visual-check`, `/user-manual` and `/video-tutorial`.

```json
{
  "app": "Acme Orders",
  "organization": "Acme Corp — Operations",
  "support": "Questions? Contact the help desk at help@example.com",
  "baseUrl": "http://localhost:8080/orders",
  "locale": "en-US",
  "hide": ["#dev-toolbar", ".cookie-banner"],
  "redact": ["td.col-email", "td.col-customer"],
  "protectedLabels": [],
  "manual": { "width": 1440, "height": 900, "scale": 2 },
  "video": {
    "output": "~/Videos/walkthroughs/acme-orders",
    "logo": "assets/logo.png",
    "primaryColor": "#1E293B",
    "accentColor": "#2563EB"
  }
}
```

| Key | Use |
|---|---|
| `app` | **Required.** Name of the app, used on covers, titles and file names. |
| `baseUrl` | **Required.** Local, dev or staging environment. Never production. Paths in `check.js` and walkthroughs are appended to it. |
| `organization` | Shown on the manual cover and footer. |
| `support` | Support contact, shown on the last video card. |
| `locale` | Browser locale (default `en-US`). Affects dates and numbers rendered by the app. |
| `hide` | Selectors hidden in every screenshot: dev toolbars, theme configurators, cookie banners, chat widgets. |
| `redact` | Selectors always blurred: personal data (names, emails, IDs, phone numbers). |
| `protectedLabels` | Extra button labels that must never be clicked without `allowChange`, e.g. for apps in other languages (`["guardar", "eliminar", "enviar"]`). English words such as save, delete, submit, send, sign, pay are built in. |
| `ignoreHttpsErrors` | `true` only for local environments with a self-signed certificate. |
| `manual` | Viewport for manual screenshots. With `scale` 2 text stays sharp in print. |
| `video.output` | Folder for the MP4 files, outside the repository. Default `~/Videos/walkthroughs/<app>/<walkthrough>/`. |
| `video.logo` | Optional PNG/JPG/SVG/WebP (relative to the config file) for the cover and closing cards. |
| `video.primaryColor` / `video.accentColor` | Optional colors for title cards and the caption bar. |
| `video.labels` | Optional caption text overrides for other languages: `{"cover": "Video walkthrough", "step": "Step", "of": "of", "end": "End of walkthrough"}`. |

The kit does not sign in or handle credentials. If the screens you need are
behind a login or any other precondition, the agent asks you how to handle it.
