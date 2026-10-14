# Project configuration

`docs/webapp-docs.json`, one per project. Used by `/visual-check`, `/user-manual` and `/video-tutorial`.

```json
{
  "app": "Acme Orders",
  "organization": "Acme Corp — Operations",
  "support": "Questions? Contact the help desk at help@example.com",
  "baseUrl": "http://localhost:8080/orders",
  "locale": "en-US",
  "login": {
    "path": "/login",
    "usernameSelector": "input[name='username']",
    "passwordSelector": "input[name='password']",
    "submitSelector": "button[type='submit']",
    "afterLoginSelector": "nav.main-menu"
  },
  "hide": ["#dev-toolbar", ".cookie-banner"],
  "redact": ["td.col-email", "td.col-customer"],
  "protectedLabels": [],
  "roles": {
    "clerk":   { "name": "Order Clerk",   "credentialsEnv": { "username": "ACME_CLERK_USER", "password": "ACME_CLERK_PASS" } },
    "manager": { "name": "Store Manager", "credentialsEnv": { "username": "ACME_MGR_USER",   "password": "ACME_MGR_PASS" } }
  },
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
| `baseUrl` | **Required.** Local, dev or staging environment. Never production. |
| `roles` | **Required.** One entry per role. `name` is the label shown in manuals and videos. |
| `roles.<id>.credentialsEnv` | **Names** of the environment variables (`username`, `password`). The values never go in the file. Omit it for roles that need no login. |
| `organization` | Shown on the manual cover. |
| `support` | Support contact, shown on the last video card. |
| `locale` | Browser locale (default `en-US`). Affects dates and numbers rendered by the app. |
| `login` | Login form selectors. Use `noNavigation: true` for SPAs that do not reload after login. Omit `login` if the app has no login. |
| `hide` | Selectors hidden in every screenshot: dev toolbars, theme configurators, cookie banners. |
| `redact` | Selectors always blurred: personal data (names, emails, IDs, phone numbers). |
| `protectedLabels` | Extra button labels that must never be clicked without `allowChange`, e.g. for apps in other languages (`["guardar", "eliminar", "enviar"]`). English words such as save, delete, submit, send, sign, pay are built in. |
| `ignoreHttpsErrors` | `true` only for local environments with a self-signed certificate. |
| `manual` | Viewport for manual screenshots. With `scale` 2 text stays sharp in print. |
| `video.output` | Folder for the MP4 files, outside the repository. Default `~/Videos/walkthroughs/<app>/<role>/`. |
| `video.logo` | Optional PNG/JPG/SVG/WebP (relative to the config file) for the cover and closing cards. |
| `video.primaryColor` / `video.accentColor` | Optional colors for title cards and the caption bar. |
| `video.labels` | Optional caption text overrides for other languages: `{"cover": "Video walkthrough", "step": "Step", "of": "of", "end": "End of walkthrough"}`. |
