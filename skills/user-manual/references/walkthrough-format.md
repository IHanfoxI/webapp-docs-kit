# Walkthrough format

`docs/manuals/<name>/walkthrough.json`, one per manual or video. The folder
name identifies it (`getting-started`, `orders`...). Used by `capture.js`
(manual) and `record.js` (video).

```json
{
  "title": "Managing orders",
  "scenes": [
    { "title": "Find an order", "steps": [
      { "go": "/orders", "text": "Open **Orders** from the menu.", "screenshot": "orders" },
      { "type": "input[name='search']", "value": "1042", "text": "Type part of the **order number** to filter the list." },
      { "click": "button.new-order", "text": "Click **New order**.", "screenshot": "new-order", "crop": "[role=dialog]", "wait": "[role=dialog]" }
    ]}
  ]
}
```

Each step has **one** action:

| Action | What it does |
|---|---|
| `"go": "/path"` | Navigates to `baseUrl + path`. The first step must be a `go`. |
| `"click": "sel"` | Clicks the element. With `"simulate": true` it only shows the click. |
| `"type": "sel"` + `"value"` | Types into the field in chunks. In the video the text appears gradually. |
| `"highlight": "sel"` | Does nothing: it only marks and explains an element. |

Options for any step:

| Option | Effect |
|---|---|
| `text` | **Required.** Explanation of the step, in the imperative. It is the video caption and the `.srt` text. `**bold**` is highlighted. About 20 words at most. |
| `mark` | Selector or list of selectors to draw the red box around. Default: the step's own element. `go` steps have no box unless set. |
| `zoom` | `false` keeps the full screen. A number sets the scale (1 to 2.2). Default: computed so the marked area fills about 60 % of the frame. |
| `wait` | Milliseconds, or a selector that must appear after the action (animated dialogs, slow AJAX). |
| `pause` | Reading time in the video, in seconds. Default: based on the text length. |
| `redact` | Extra selectors blurred on this step. |
| `screenshot` | Name of the manual PNG, taken **after** the step. |
| `crop` | Crops the manual screenshot to this element. |
| `fullPage` | Manual screenshot of the whole page. |
| `pressEnter` | On `type`: press Enter afterwards. Only for search and filter boxes. |
| `simulate` | On `click`: shows the click without performing it. Use it on buttons that save, delete, send, sign or pay. |
| `allowChange` | Allows clicking a button that changes data. Only with explicit authorization and in a test environment. |

The kit does not sign in. If the screens are behind a login or another
precondition, ask the user how to handle it before writing the walkthrough.

If the next step depends on a simulated click (for example the confirmation
dialog of Delete), the walkthrough cannot show it. End the scene at the
simulated click and explain the result in its text.
