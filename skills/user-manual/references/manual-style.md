# User manual style guide

Every manual has the same structure, tone and format. Leave out sections that do not apply.

## Structure

The cover, the table of contents, the header and the footer come from the
template. The author writes from the preface on.

| Section | Content |
|---|---|
| Preface (*About this manual*) | One paragraph: which part of the app it covers, who it is for, and the topics included. A second paragraph: what is out of scope (other manuals) and a note that screenshots are illustrative and personal data is blurred. |
| 1. Introduction | 1.1 Purpose: which process the app supports. 1.2 What you can do: bullets starting with a verb. |
| 2. Getting started | 2.1 Opening the app: browser and address (and how to sign in, if the app has sign-in). 2.2 Home page: figure and a table of its sections. 2.3 Navigation: table Option / Description. |
| 3 to N. Features | One section per task, in the order users perform them. |
| Second to last (optional) | Reports, email notifications and other cross-cutting features. |
| Last: Tips and support | Good practices, common mistakes and who to contact. |

## Each feature

1. A context paragraph: what it is and how to get there.
2. For a procedure, steps `a)`, `b)`, `c)` in the imperative:
   "Click **New order**", "Select the customer".
3. A figure of the screen.
4. A **Field / Description** table. Required fields end with ` *`.
   For buttons in a table, use **Button / Action**.
5. A `> **Important:** ...` note for restrictions: what cannot be done, in
   which state an action becomes available, or who can do it.

## Writing

- Address the reader as **you**, in the imperative: "Click", "Select", "Enter".
- Write the names of buttons, menus, columns and states in bold, exactly as
  they appear on screen.
- Keep sentences short. One action per step.
- Name icons by their shape and tooltip: "Eye (View)", "Pencil (Edit)".
- Do not describe how the system works internally: no database tables,
  services, endpoints or class names.
- Avoid developer jargon: write "window", not "modal"; "list", not "grid".

## Figures

- Each figure shows a single idea. Crop dialogs and panels with `"crop"`.
- The caption is a sentence with a final period. "Figure N." is added automatically.
- Use the red box (`"mark"`) only when the text refers to a specific element
  that is hard to find.
- Always blur personal data.

## File names

`docs/manuals/<name>/manual-<app>-<name>.pdf`, lowercase, no accents or spaces.
Example: `manual-acme-orders-getting-started.pdf`.
