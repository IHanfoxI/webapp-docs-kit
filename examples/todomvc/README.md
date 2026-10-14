# Example: TodoMVC

Documents the public [Playwright TodoMVC demo](https://demo.playwright.dev/todomvc).
It needs no setup, so it is a quick way to see what the skills produce.

| File | What it is |
|---|---|
| [`docs/webapp-docs.json`](docs/webapp-docs.json) | Project config |
| [`docs/manuals/getting-started/walkthrough.json`](docs/manuals/getting-started/walkthrough.json) | Two scenes, six steps, four screenshots |
| [`docs/manuals/getting-started/manual.md`](docs/manuals/getting-started/manual.md) | Manual text written from the screenshots |
| [`manual-todomvc-getting-started.pdf`](https://github.com/IHanfoxI/webapp-docs-kit/releases/latest/download/manual-todomvc-getting-started.pdf) | Generated manual (release download; generated files are not committed) |

Open a terminal in this folder, start your agent and ask:

```text
/user-manual getting started
/video-tutorial getting started
```

The demo stores its list in the browser, so adding and completing tasks here
changes nothing on a server. On a real app those steps would use `"simulate": true`.
