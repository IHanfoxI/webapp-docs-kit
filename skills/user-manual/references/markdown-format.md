# Manual Markdown format

`build_manual.py` accepts this subset of Markdown. Anything else is treated as a
paragraph.

```markdown
---
app: Acme Orders
subtitle: Getting started
organization: Acme Corp — Operations
title: User manual
date: October 2026
---
Preface text. It goes before the first "#" and may have several paragraphs.

# Introduction

## Purpose

Paragraph with **bold**, *italic* and `code`.

- Bullet
- Another bullet

a) Step one (also accepts "1.")
b) Step two

![The new order form.](screenshots/new-order.png)

| Field | Description |
|---|---|
| Customer * | Who places the order. |

> **Important:** an order cannot be created without a customer.

\newpage
```

| Element | Result |
|---|---|
| front matter | Cover: `title` (default "User manual"), `app`, `subtitle` (optional, e.g. the topic or audience), `organization` and `date` (default: current month and year). Only `app` is required. Also `preface_title` (default "About this manual"), `contents_title` (default "Contents") and `figure_label` (default "Figure") for manuals in other languages. |
| `#` | Heading 1, numbered automatically ("1. Introduction"), with an accent line and a table of contents entry. |
| `##` | Heading 2, numbered automatically ("1.1 Purpose"), in the table of contents. |
| `###` | Heading 3, not numbered, not in the table of contents. |
| `- ` | Template bullets. |
| `a)` / `1.` | Lettered list a), b), c)… that restarts on every list. |
| `![caption](path.png)` | Centered figure, at most 15.5 cm wide (11.9 cm tall), with a thin gray border and the caption "Figure N. caption". PNG only. The path is relative to the `.md`. |
| table | Header row in the template's primary color with white text. Column widths proportional to content. |
| `>` | Highlighted note: gray background and an accent bar. |
| `\newpage` | Page break. |

Do not write section numbers: they are computed.
