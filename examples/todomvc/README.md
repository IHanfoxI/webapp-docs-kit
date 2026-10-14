# Example: TodoMVC

Documents the public [Playwright TodoMVC demo](https://demo.playwright.dev/todomvc).
No login and no credentials are needed, so it is a quick way to see what the
skills produce.

| File | What it is |
|---|---|
| [`docs/webapp-docs.json`](docs/webapp-docs.json) | Project config: one public `visitor` role |
| [`docs/manuals/visitor/walkthrough.json`](docs/manuals/visitor/walkthrough.json) | Two scenes, six steps, four screenshots |
| [`docs/manuals/visitor/manual.md`](docs/manuals/visitor/manual.md) | Manual text written from the screenshots |
| [`docs/manuals/visitor/manual-todomvc-visitor.pdf`](docs/manuals/visitor/manual-todomvc-visitor.pdf) | Generated manual |

Open a terminal in this folder, start your agent and ask:

```text
/user-manual visitor
/video-tutorial visitor
```

The demo stores its list in the browser, so adding and completing tasks here
changes nothing on a server. On a real app those steps would use `"simulate": true`.
