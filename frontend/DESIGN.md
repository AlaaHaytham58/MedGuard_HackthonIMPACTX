---
name: MedGuard
description: A clinical-verdict medication-safety checker for elderly and non-technical caregivers — structural navy, one rationed verdict color, and a legibility-first type system.
colors:
  navy-950: "#071527"
  navy-900: "#0b2340"
  navy-800: "#123055"
  navy-700: "#1c4270"
  navy-600: "#2a5490"
  navy-500: "#3d6bad"
  navy-200: "#b9cde3"
  navy-100: "#dbe6f4"
  navy-50: "#eef3fa"
  bg: "#f4f7fb"
  surface: "#ffffff"
  surface-sunken: "#eef2f7"
  border: "#d7e0ea"
  border-strong: "#b9c8d9"
  ink: "#0d1e33"
  ink-muted: "#4c6079"
  ink-faint: "#5b7089"
  ink-on-navy: "#f4f8fc"
  ink-on-navy-muted: "#a9c0da"
  green-800: "#146c43"
  green-700: "#1a8452"
  green-100: "#e1f5e9"
  green-ink: "#0e3d28"
  green-border: "#a9dcbf"
  red-800: "#a3271f"
  red-700: "#c33a2f"
  red-100: "#fbe8e6"
  red-ink: "#5c1712"
  red-border: "#eab3ac"
typography:
  headline:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 1.4rem + 1.4vw, 2.35rem)"
    fontWeight: 700
    lineHeight: 1.15
  title:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 700
    lineHeight: 1.15
  body:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 600
    letterSpacing: "0.06em"
rounded:
  sm: "10px"
  md: "16px"
  lg: "22px"
  pill: "999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "22px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.navy-900}"
    textColor: "{colors.ink-on-navy}"
    rounded: "{rounded.pill}"
    padding: "13px 22px"
  button-primary-hover:
    backgroundColor: "{colors.navy-800}"
  button-secondary:
    backgroundColor: "{colors.navy-50}"
    textColor: "{colors.navy-900}"
    rounded: "{rounded.pill}"
    padding: "13px 22px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.navy-700}"
    rounded: "{rounded.pill}"
    padding: "13px 22px"
  button-outline:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.navy-900}"
    rounded: "{rounded.pill}"
    padding: "13px 22px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "28px"
  pair-pill:
    backgroundColor: "{colors.navy-900}"
    textColor: "{colors.ink-on-navy}"
    rounded: "{rounded.pill}"
    padding: "7px 16px"
---

# Design System: MedGuard

## Overview

**Creative North Star: "The Clinical Verdict"**

MedGuard reads as a medical instrument, not a chat product or a metrics dashboard. It explicitly refuses the AI-chatbot bubble-and-avatar template and the KPI-card-grid template that this category defaults to — no avatars, no floating message bubbles, no colored stat tiles. Structure (fixed order: pair → verdict → detail grid → history) carries the trust; color is spent once, on the one moment it must mean something.

The palette is a single structural navy over a near-white cool-neutral ground, applied with generous corner radii, pill-shaped controls, and soft ambient shadows — confident and calm rather than alarmed, because the audience named in PRODUCT.md is elderly and non-technical and the product's job is to lower anxiety, not raise it with clinical-red chrome everywhere. Atkinson Hyperlegible Next is used throughout for genuine low-vision legibility, not as a stylistic choice, and is self-hosted (`@fontsource`) for offline reliability. A single hand-drawn stroke icon set (1.6px, round joins) stands in for both illustration and iconography; there is no icon font and no emoji.

**Key Characteristics:**
- One structural color (navy) carries all non-verdict UI: nav, headings, buttons, pills, borders, focus rings.
- Green and red exist nowhere except the Results verdict banner and its echo (history-list status dots) — confirmed by source: `--red-*`/`--green-*` custom properties are declared once in `index.css` and consumed only in `Results.css`.
- Pill shapes (999px radius) for every actionable control; generous card radii (16–22px) for containers.
- Errors and invalid states are shown via icon + weight + border, never via color — the color-rationing rule extends to failure states, not just success/danger.

## Colors

A near-monochrome navy system over a cool-white ground, with color intentionally rationed to a single semantic moment.

### Primary
- **Structural Navy** (`#0b2340`, `navy-900`): nav bar background, all headings (h1–h4), primary button fill, pair-name pills, dropzone icon accents, focus-ring hue family. This is the only color that appears on every screen.

### Secondary
- **Deep Navy** (`#071527`, `navy-950`): nav bottom hairline, darkest text-on-navy contrast anchor.
- **Mid Navy** (`#2a5490`–`#3d6bad`, `navy-600`/`navy-500`): interactive accents — dropzone active border, focus outline (`navy-600`), caret color, hover states on ghost/secondary controls.
- **Pale Navy** (`#eef3fa`–`#dbe6f4`, `navy-50`/`navy-100`): tinted surfaces for the disclaimer note, secondary-button fill, active nav-link chip, hover backgrounds. Never a warning color — the disclaimer is explicitly "quiet navy-tinted," not amber or red.

### Tertiary (verdict-only; confined to Results)
- **Verdict Green** (`#1a8452` / bg `#e1f5e9`, `green-700`/`green-100`): the safe-verdict banner fill, its icon, and the "safe" history-list dot. Does not appear anywhere outside `Results.css`.
- **Verdict Red** (`#c33a2f` / bg `#fbe8e6`, `red-700`/`red-100`): the danger-verdict banner fill, its icon, and the "danger" history-list dot. Does not appear anywhere outside `Results.css`.

### Neutral
- **Cool-Neutral Ground** (`#f4f7fb`, `bg`): page background, the only background color a user sees before scrolling to a colored surface.
- **Card White** (`#ffffff`, `surface`): panels, inputs, history items.
- **Sunken Surface** (`#eef2f7`, `surface-sunken`): recessed rows inside panels (photo chip, ingredient list rows) — one step darker than card white, used to imply nesting without a border.
- **Hairline Border** (`#d7e0ea`, `border`) / **Strong Border** (`#b9c8d9`, `border-strong`): panel edges and dashed dropzone stroke respectively.
- **Navy-Tinted Ink** (`#0d1e33` body / `#4c6079` muted / `#5b7089` faint): all text is tinted from navy, never true gray — this is a deliberate, systemic choice (`index.css` comment: "Text — tinted from navy, never gray").

### Named Rules
**The Verdict-Only Color Rule.** Green and red exist nowhere except the Results verdict banner and the history-list dots that echo it. Every other surface, including all error and invalid states, communicates in navy, ink, and border weight only. Before adding a `--red-*`/`--green-*` reference anywhere outside `Results.css`, confirm it is a verdict, not a warning.

**The Tinted-Never-Gray Rule.** Neutral text and borders are always a navy tint (`ink`, `ink-muted`, `ink-faint`, `border`, `border-strong`), never a true achromatic gray — this keeps the one-hue-family discipline even in "neutral" content.

## Typography

**Body Font:** Atkinson Hyperlegible Next (with Segoe UI, system-ui, sans-serif fallback)

**Character:** A single legibility-first humanist sans used for every role — display, body, and label alike. There is no separate display or mono face; hierarchy comes from weight and size, not typeface switching, which keeps the low-vision legibility promise consistent everywhere.

### Hierarchy
- **Headline** (700, `clamp(1.75rem, 1.4rem + 1.4vw, 2.35rem)`, 1.15 line-height): the Home page h1 and equivalent top-of-page headings.
- **Title** (700, 1.05rem, 1.15 line-height): panel and section headings (`panel__heading`, `dropzone__title`).
- **Body** (400, 17px base / 1rem–1.08rem in context, 1.55 line-height): lede copy, disclaimer text, report prose (`report-text`); lede is capped at 52ch, disclaimer at default paragraph measure.
- **Label** (600–700, 0.85–0.94rem, uppercase + 0.06em tracking for the "or" divider only): field labels, chip meta, ingredient names, history timestamps. Uppercase tracking is reserved for the single `divider` component, not used as a general label treatment.

### Named Rules
**The One-Face Rule.** Every text role — heading, body, label — is Atkinson Hyperlegible Next. No secondary display or system face is introduced for emphasis; emphasis comes from weight (400/600/700/800) and size only, preserving legibility for the low-vision audience PRODUCT.md names as primary.

## Layout

Both pages are centered single columns on the cool-neutral ground, not full-bleed dashboards. Home caps at 640px max-width (`--font-body` copy measure plus room for the dropzone); Results widens to 860px to host the two-column detail grid. Vertical rhythm is a consistent 20–22px gap between stacked sections (`.home`, `.results` both use `gap: 22px`/`20px`), with panels internally padded at 28px. Results' detail grid (`report-grid`) is `1fr 1fr` on desktop and collapses to a single column under 720px; Home's search form goes column-on-mobile under 520px. There is no sidebar, hero image, or marketing chrome on either page — confirmed by the direction contract and the shipped markup.

## Elevation & Depth

Flat-by-default with one soft ambient card shadow used structurally, not decoratively. A single shadow token (`--shadow-card`) is applied to every `.panel`, `.history-item`'s resting state stays borderless-flat, and the verdict banner itself carries no shadow at all — its weight comes from full-width colored fill, not elevation. Depth is otherwise conveyed by surface layering (white panel over `surface-sunken` rows over `bg`), not by z-axis shadow stacking.

### Shadow Vocabulary
- **Card** (`box-shadow: 0 1px 2px rgba(11,35,64,0.06), 0 8px 24px -12px rgba(11,35,64,0.18)`): the only shadow in the system; applied to every `.panel` (upload panel, search panel, report-grid cards).

### Named Rules
**The One-Shadow Rule.** There is exactly one shadow token in the build. It marks "this is a raised panel"; nothing else in the system uses elevation to communicate state or hierarchy.

## Shapes

Generous, consistently rounded geometry with no sharp corners anywhere in the shipped UI. Three radius steps are used by role: 10px (`--radius-sm`) for small nested elements (photo thumbnail, ingredient rows), 16px (`--radius-md`) for mid-size containers (disclaimer, dropzone, photo chip, history items), and 22px (`--radius-lg`) for top-level panels and the verdict banner. Every actionable control — buttons, pills, the search input, the icon button, nav links — uses a full 999px pill radius, which is the system's strongest recurring silhouette. Borders are thin (1–1.5px) and low-contrast (`border`/`border-strong`) except the dropzone, which uses a 2px dashed stroke as its only textural departure, and the `aria-invalid` search input, which doubles its border to 2px navy instead of changing color.

## Components

### Buttons
- **Shape:** full pill (`border-radius: 999px`), 13px/22px padding, 1.5px border (transparent on primary/secondary, visible on ghost/outline).
- **Primary:** navy-900 fill, ink-on-navy text; hover darkens to navy-800. Used once per form as the single committing action (Check interactions).
- **Hover / Focus:** background-only hover transition (0.15s); focus uses the global 3px navy-600 outline with 2–3px offset, not a button-specific ring.
- **Secondary / Ghost / Outline:** secondary is navy-50 fill with navy-100 border (Choose photo); ghost is transparent with a strong border (Take a photo); outline is white fill with a navy-800 border (search submit). All three exist to rank actions by commitment without introducing a second color.

### Cards / Containers
- **Corner Style:** 22px (`panel`, verdict banner), 16px (disclaimer, dropzone, photo chip, history item), 10px (ingredient row, thumbnail).
- **Background:** white (`surface`) for panels and history items; `surface-sunken` for nested rows; `navy-50` for the disclaimer.
- **Shadow Strategy:** the single card shadow (see Elevation) on `.panel` only; nested rows and history items are flat with a border instead.
- **Border:** 1px `border` on panels/history items; 1px `navy-100` on the primary panel and disclaimer.
- **Internal Padding:** 28px (panel), 16–18px (disclaimer, history item), 12–14px (nested rows).

### Inputs / Fields
- **Style:** pill-radius (999px) text input with a 1.5px `border-strong` stroke, leading icon inset at 46px.
- **Focus:** the global focus-visible outline (3px navy-600, 3px offset) — no separate glow or shadow treatment.
- **Error:** communicated by border weight and icon, never color — `[aria-invalid="true"]` doubles the border to 2px navy-900; the accompanying `.field-error` message uses navy text with an `AlertIcon`, not red. This is a deliberate, load-bearing choice to protect the verdict-only color rule.

### Navigation
- **Style:** sticky navy-900 bar, ink-on-navy brand text with a muted subtitle; nav links live in a pill-shaped dark-well (`rgba(0,0,0,0.18)`) with the active link inverted to a light pill (`ink-on-navy` fill, navy-900 text). Mobile drops the brand subtitle and tightens padding under 480px; no hamburger menu — the link set is small enough to stay inline.

### Verdict Banner (signature component)
The one full-saturation moment in the product. A full-width, 22px-radius band with a 1.5px tinted border, colored fill (red-100/green-100), icon (AlertIcon/CheckCircleIcon) in the matching 700-weight hue, an 800-weight headline, and a muted timestamp. It is deliberately not a shadowed, floating card — it sits flush in the page flow immediately below the drug-name pills, reading as a verdict stamp rather than a notification toast. The history-list status dots (10px filled circles) are the only other place these two hues appear, explicitly designed to echo the banner so the session history reads as a legible ledger of past verdicts.

## Do's and Don'ts

### Do:
- **Do** keep navy as the only structural color across chrome, headings, and primary actions (`navy-900` / `navy-800` / `navy-600`).
- **Do** use full pill radius (999px) for every interactive control (buttons, inputs, pills, nav links).
- **Do** communicate error/invalid state via icon + border weight + weight, never via a color shift (see `.field-error`, `[aria-invalid="true"]`).
- **Do** confine red and green strictly to the Results verdict banner and its history-dot echo.
- **Do** set body and heading text in Atkinson Hyperlegible Next at every weight; do not introduce a second face for emphasis.

### Don't:
- **Don't** introduce red or green anywhere outside `Results.css` — this was an explicit finish-review finding (3 leaks caught and fixed) and is now an enforced boundary, verified by grep against `--red-`/`--green-` usage at documentation time.
- **Don't** use amber/yellow or red as a "quiet" warning tint on Home; the disclaimer note is navy-tinted (`navy-50`/`navy-800`) precisely so it doesn't compete with the verdict.
- **Don't** add drop shadows beyond the single `--shadow-card` token, or use shadow to indicate interactive state — hover/focus are communicated by background and border-color shifts only.
- **Don't** add kickers, eyebrows, or uppercase-tracked section labels beyond the one existing "or" divider; none exist in the shipped build and none should be inherited as a pattern.
