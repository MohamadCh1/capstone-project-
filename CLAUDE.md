# CSS Refactor — In-Progress Task Status

## 1. Task in progress

Extracting all inline `<style>` blocks and the shared `static/styles.css` into one
clearly-named CSS file per template (in `static/css/`), with clearer selector names
where the originals were vague, then deleting `static/styles.css` entirely once its
content has been fully redistributed.

## 2. Current status

**Step 2 is complete.** Per-template CSS files have been created in `static/css/`:

- `home.css`
- `patient_login.css`
- `patient_register.css`
- `doctor_login.css`
- `doctor_register.css`
- `device_change.css`
- `doctor_dashboard.css`
- `patient_dashboard.css`
- `patient_info.css`
- `devices_dashboard.css`
- `ask_ai.css`

All 11 templates now link their new CSS file, and all old inline `<style>` blocks
have been removed from every template.

The old `<link rel="stylesheet" href="/static/styles.css">` tags are **still in
place** on the 7 templates that originally had them (`home.html`,
`patient_login.html`, `patient_register.html`, `doctor_login.html`,
`doctor_register.html`, `device_change.html`, `doctor_dashboard.html`) —
left there **deliberately** as a safety net until visual verification is confirmed.

`static/styles.css` itself is **untouched** — 711 lines, unmodified.

## 3. Decisions already made and locked in (do NOT re-ask about these)

- **D1**: Body-padding leaks on `device_change.html`, `home.html`, and
  `doctor_dashboard.html` — where a bare `body{}` rule in `styles.css` was leaking
  properties (e.g. `padding: 40px`) into pages that appeared to fully override body
  styling via a class or inline block — were **flattened into one clean rule per
  file**, not preserved as literal cross-file leaked lines. Visual output is
  identical either way; this only changes how it's expressed in code.
- **Extended D1 principle**: Two additional, same-category leaks were found and
  flattened the same way while assembling the files: `.cd-btn` (now
  `.device-change-submit-button`) and `.availability-btn` were both inheriting
  `width`/`margin-top`/`padding` from `styles.css`'s bare `button{}` rule (and
  `.cd-btn` even currently swaps to a different **hover** background color due to a
  specificity quirk against `button:hover`). Both are flattened and **kept as-is,
  not reverted** — confirmed by the user.
- **Decision E**: `patient_info.html` uses `medsys-app`, `medsys-title`, and
  `medsys-subtitle` classes that resolve to **zero CSS rules** today (they were
  never linked to `styles.css`, and its own inline block never defined them). Per
  explicit decision, `patient_info.css` adds **zero new rules** for these three —
  current (effectively unstyled) rendering is preserved exactly, not "fixed."
- **Renaming scope**: CSS selectors were renamed for clarity **only** where the
  existing name was genuinely vague/cryptic (e.g. `.cd-btn` →
  `.device-change-submit-button`, `.msg` → `.chat-bubble`). Already-clear or
  intentionally-shared names were deliberately left unrenamed: `.form-container`,
  `.switch-link`, `.error`, `.message`, the base `body`/`h1`/`label`/`input,
  select`/`button` selectors, and the entire `medsys-*` naming system in
  `doctor_dashboard.html`/`patient_info.html`.

### Full rename log (old → new, by file)

| File | Old selector | New selector |
|---|---|---|
| `device_change.html` | `.cd-body` | `.device-change-page` |
| `device_change.html` | `.cd-container` | `.device-change-container` |
| `device_change.html` | `.cd-header` | `.device-change-header` |
| `device_change.html` | `.cd-card` | `.device-change-card` |
| `device_change.html` | `.cd-form` | `.device-change-form` |
| `device_change.html` | `.cd-field` (×3) | `.device-change-field` |
| `device_change.html` | `.cd-btn` | `.device-change-submit-button` |
| `ask_ai.html` | `.msg` | `.chat-bubble` |
| `ask_ai.html` | `.user-msg` | `.chat-bubble-user` |
| `ask_ai.html` | `.ai-msg` | `.chat-bubble-ai` |
| `patient_dashboard.html` | `.main-grid` | `.dashboard-content-grid` |
| `patient_dashboard.html` | `.card` (×2) | `.dashboard-panel` |
| `patient_dashboard.html` | `.card-title` (×2) | `.dashboard-panel-title` |
| `patient_dashboard.html` | `.sug-head` | `.suggestion-head` |
| `patient_dashboard.html` | `.sug-priority` | `.suggestion-priority-badge` |
| `patient_dashboard.html` | `.sug-text` (×2) | `.suggestion-text` |

(`ask_ai.html`'s rename also required updating two JS `className` assignments in
its embedded `<script>` block — already done, not just the HTML markup.)

## 4. What's blocking progress

The user is manually visually verifying every page/state renders identically to
before the refactor, using a provided checklist (one URL/state per template,
including the two-state templates `patient_dashboard.html` and `patient_info.html`
which have both an empty-data state and a with-data state to check).

**Step 3** (remove the now-redundant old `<link rel="stylesheet"
href="/static/styles.css">` tags from the 7 templates that still have them) and
**Step 4** (delete `static/styles.css` entirely) are **BLOCKED** until the user
gives explicit go-ahead that the visual check passed.

## 5. Instruction for any future session reading this file

- Do **not** redo Step 1 (inventory) or Step 2 (file creation/renaming/linking) —
  they are complete and verified against the code.
- Do **not** re-ask about decisions D1, E, the extended-leak-flattening decision, or
  the renaming scope — they are settled per section 3 above.
- Only proceed to Step 3/4 once the user explicitly confirms the manual visual
  check passed. Until then, take no further action on this task beyond what's
  asked.
