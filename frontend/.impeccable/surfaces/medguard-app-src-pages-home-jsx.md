---
version: 1
slug: "medguard-app-src-pages-home-jsx"
primary_target: "medguard-app/src/pages/Home.jsx"
related_targets: ["medguard-app/src/pages/Results.jsx"]
---

## Direction contract

THESIS: A medication-safety check reads as a clinical verdict, not a chat answer or a dashboard metric — the page refuses the AI-chatbot bubble-and-avatar template and the KPI-dashboard card grid that this category defaults to. Structure carries trust; color is rationed to the one moment it must mean something.

OWN-WORLD: Navy (#0b2340 family) as the sole structural color — nav bar, headings, primary buttons, pills, borders — over a near-white, cool-neutral ground (#f4f7fb). Atkinson Hyperlegible Next throughout, chosen for genuine low-vision legibility, not aesthetic novelty — this audience is explicitly elderly/non-technical per PRODUCT.md. Generous corner radii (16–22px), soft card shadows, pill-shaped buttons and nav. Hand-drawn single-stroke icon set (1.6px, round joins) — no emoji, no icon-font. Green/red exist nowhere except the Results verdict banner and the history dots that echo it; everywhere else is navy-on-neutral.

STORY: The visitor arrives worried about a real medicine interaction. Home asks for exactly one thing (a photo or a name) and states plainly, before any input, that the AI reads names but a verified database renders the verdict. Submitting shows a brief, honest "reading/looking that up" state, then Results opens already resolved: the pair named at the top, a verdict banner impossible to misread, then the ingredients/why/what-to-do/alternatives in that fixed order, then a session history of past checks so the visitor can see this isn't a black box.

FIRST VIEWPORT (Home): centered single column, max 640px. Heading + one-line lede, then the safety disclaimer as a quiet navy-tinted note (not a warning color), then the upload panel as the visually heaviest element (dashed dropzone, upload-cloud icon, two actions), an "or" rule, then the text-search fallback panel, visually lighter than the upload panel. No sidebar, no hero image, no marketing chrome.

FIRST VIEWPORT (Results): drug-name pills, then the verdict banner immediately below — full width, colored fill (red or green tint) with icon + headline + timestamp, the only saturated color on the page. Below it a two-column detail grid (ingredients / why / what-to-do / alternatives), then a plain list-style history panel.

FORM: user-pinned direction from an explicit written brief plus four reference screenshots (treated as component/layout reference only — card shapes, badges, dropzone, detail-card structure — not as color or step-count authority, which the user's navy/2-page spec overrides). No concept-seed roll: the brief was specific enough to be a pinned direction, not an open creative choice. No image generation available in this session, so the build is code-led by necessity — no comp exists to measure against; ambition is carried in this contract instead.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.
