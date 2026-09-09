# MedGuard — Extreme Execution Plan
**IMPACT 2026 · Healthcare Track · Team of 4**

This is built for your exact situation: **2 prep days before**, then the actual hackathon **8:00–17:00, two days** (18 working hours onsite). Everything front-loadable is pushed into prep so hackathon hours go 100% into building, debugging, and rehearsing the demo — not setup.

---

## 0. Non-negotiable scope lock

Your proposal is strong because it's honest about what AI does vs. what a database does. Don't let scope creep blur that on stage. The MVP is exactly three steps, chained:

`Photo(s) → Gemini Vision (extract names) → LLM (normalize to generic) → DDInter 2.0 lookup (deterministic interaction check) → one-page plain-language summary`

**MUST have for demo:** upload 2-4 photos → extracted drug list → normalized generics → flagged duplicate/interaction → printable one-pager.
**SHOULD have:** openFDA fallback when DDInter has no match, graceful handling of unrecognized Egyptian brands.
**CUT if behind:** multi-language UI, user accounts, history/save, mobile app wrapper (web is fine), fancy animations.

Keep a visible "MUST / SHOULD / CUT" list pinned somewhere (Notion/whiteboard) — update it every sync.

---

## 1. Roles (assign now, keep fixed)

The AI Pipeline was originally one role, but it's genuinely two separate hard problems (vision is a different beast from normalization/mapping), so it's split across two people. There's no standalone "integration/demo" role — those duties are folded into the two roles that naturally touch them, so nobody is sitting idle.

| Role | Owns | Suggested person |
|---|---|---|
| **A1 — Vision Extraction** | Gemini Vision integration, image preprocessing (glare/blur handling), the `/extract` endpoint, and sourcing/shooting the real demo photos (closely tied to what the vision model needs to handle well) | Strong with LLM/vision API work |
| **A2 — Normalization** | RxNorm API integration, the Egyptian brand-name lookup table (30-40 entries), LLM fallback mapping for anything not covered, the `/normalize` endpoint, and later the plain-language explanation prompt for the one-pager | Strong with prompt engineering (your Hindawi RAG background fits well here) |
| **B — Interaction Engine + Orchestration** | DDInter 2.0 ingestion into SQLite, matching logic, openFDA fallback, the `/check` endpoint, chaining all three endpoints into one working `/pipeline`, and backend deployment (Railway) | Comfortable with pandas/SQL and backend plumbing |
| **C — Frontend + Demo Ops** | Upload/camera UI, results screen, printable one-pager, frontend deployment (Vercel), the offline cached-fallback JSON, coordinating dry runs, and the pitch deck | Strongest React person, ideally also comfortable presenting |

Everyone still codes on their own piece — these are ownership, not silos. Stand up every 2 hours, 5 minutes, no exceptions: what's done, what's blocked, what's next.

---

## 2. Stack decision (lock this in prep, don't relitigate mid-hackathon)

- **Backend:** Python + FastAPI — fastest for chaining API calls (Gemini, RxNorm, openFDA) and for pandas-based DDInter processing. Avoid .NET here purely for hackathon speed, even though it's a known strength — Python's ecosystem for this exact task (LLM calls + tabular interaction data) will save hours.
- **Frontend:** React (Vite), deployed to Vercel.
- **DDInter storage:** load the bulk download into a local **SQLite** file at build time (not live scraping/querying their site) — instant, offline-safe, no rate limits during the demo.
- **Backend hosting:** Railway.

---

## 3. PREP DAY 1 (T-2)

Goal: every external API proven to work in isolation, before you try to chain them.

| Time block | Task | Owner |
|---|---|---|
| Hr 1 | Get Gemini API key. Take 8-10 real photos of medication boxes/strips (yours, family's) in varied lighting — this becomes your test set AND your demo material. | Everyone (A1 coordinates what's needed) |
| Hr 1-2 | Test raw Gemini Vision call on 3 photos: does it reliably extract drug names from Egyptian packaging? Note failure patterns (glare, small font, Arabic text). | A1 |
| Hr 1-3 | Download DDInter 2.0 bulk file. Write a script to load it into SQLite with an indexed table `(drug_a, drug_b, severity, description)`. Confirm a known pair (e.g. an NSAID + an anticoagulant) returns a hit. | B |
| Hr 2-4 | Curate the 30-40 entry Egyptian brand → generic active ingredient table. Prioritize the meds you actually photographed plus common chronic-disease drugs (Concor→bisoprolol, Glucophage→metformin, Panadol→paracetamol, Brufen→ibuprofen, etc.). | A2 |
| Hr 2-4 | Low-fi wireframe (can be straight in React, skip Figma): 3 screens — Upload, Processing, Results/One-Pager. | C |
| Hr 3-4 | Repo setup: frontend deploy skeleton on Vercel (confirm an empty page ships to a public URL). | C |
| Hr 3-4 | Backend deploy skeleton on Railway (confirm an empty FastAPI app ships to a public URL). | B |
| Hr 4-5 | Draft pitch skeleton: problem → why existing solutions fail → AI's exact role (vision + normalization, NOT the safety verdict) → demo → ask. Write the one-line pitch verbatim on a slide. | C |
| Hr 5-6 | RxNorm API test: confirm you can map a generic name string to a standard RxNorm ingredient ID for at least 5 test drugs. | A2 |

**End of Day T-2 checkpoint:** Gemini Vision works standalone, DDInter lookup works standalone, RxNorm works standalone, repo deploys empty pages to production URLs.

---

## 4. PREP DAY 2 (T-1)

Goal: a rough end-to-end pipeline works on your machine, even if ugly.

| Time block | Task | Owner |
|---|---|---|
| Hr 1-3 | Backend skeleton: `/extract` (photo→names via Gemini). | A1 |
| Hr 1-3 | Backend skeleton: `/normalize` (names→generics via RxNorm + brand table + LLM fallback for anything not in either). | A2 |
| Hr 1-3 | Backend skeleton: `/check` (generics→DDInter matches + openFDA fallback). | B |
| Hr 1-3 | Frontend: working upload component (drag/drop + camera capture on mobile), loading state, results table shell rendering dummy JSON. | C |
| Hr 3-5 | **First full chain test**: real photo in → real one-pager data out. B leads wiring the three endpoints together into one `/pipeline` call. This is the single most important milestone before the hackathon starts — expect it to break, that's the point of doing it now. | A1 + A2 + B + C |
| Hr 5-6 | Cache the exact API responses for your 2-3 best demo photos (the ones with a real interaction) to a local JSON file. This is your **offline demo fallback** if venue wifi dies on stage — non-negotiable safety net. | C |
| Hr 5-6 | Pitch dry run #1, timed, whole team present. | C leads, all rehearse |

**End of Day T-1 checkpoint:** one real photo pair, run through the real pipeline, produces a real flagged interaction on screen. Cached fallback JSON saved.

---

## 5. HACKATHON DAY 1 (8:00–17:00)

| Time | Block | Focus |
|---|---|---|
| 8:00–8:30 | Kickoff | Confirm track/room assignment, re-read any onsite judging rubric, re-lock MUST/SHOULD/CUT, 4-person standup |
| 8:30–10:30 | Sprint 1 | **A1:** harden `/extract` — handle blurry/glare photos, retry logic, shoot more demo photos onsite. **A2:** finalize `/normalize` including LLM fallback for unrecognized brands. **B:** finalize `/check` merging DDInter + brand table + openFDA fallback. **C:** wire real upload flow to real backend (kill dummy JSON), test frontend on an actual phone |
| 10:30–10:45 | Sync | 5-min standup, re-triage bug list |
| 10:45–13:00 | Sprint 2 | Full chain integration: photo → extract → normalize → check, rendered live in the UI. **B** leads the orchestration; everyone debugs their own piece as errors surface. Get this working end-to-end with at least one real interaction flag showing on screen — protect this block fiercely |
| 13:00–13:45 | Lunch | Working lunch OK, but actually eat |
| 13:45–16:00 | Sprint 3 | **A2** writes the plain-language explanation prompt ("These two medications should not be taken together because…"). **C** builds the one-pager output — print-friendly CSS, PDF export/clean printable view. **A1** keeps hardening vision edge cases found from the morning's new photos. **B** stabilizes the backend |
| 16:00–17:00 | Wrap | End-to-end smoke test with 3 different real medication sets. Log every bug found. Tag a git commit as `day1-safe-checkpoint`. Write tomorrow's punch list before leaving |

**Day 1 exit criteria:** a stranger can upload 3 photos and get a correct one-pager, even if it looks unstyled.

---

## 6. HACKATHON DAY 2 (8:00–17:00)

| Time | Block | Focus |
|---|---|---|
| 8:00–8:15 | Standup | Re-triage punch list into MUST/SHOULD/CUT — be ruthless, today is about a working demo, not new features |
| 8:15–10:00 | Bug-fix sprint | **A1:** remaining OCR failure cases. **A2:** unrecognized-brand handling must fail gracefully, never crash. **B:** openFDA fallback trigger path |
| 10:00–11:30 | Completion sprint | **B** deploys final backend to Railway. **C** deploys final frontend to Vercel and tests on a real phone over real (not venue) wifi. **A1+A2** polish plain-language wording together for a non-technical elderly-caregiver audience |
| 11:30–11:45 | Break | |
| 11:45–13:00 | **Dry run #1** | Full stage simulation, whole team: someone plays "judge," you run the actual demo end to end, timed. Fix only what's demo-critical |
| 13:00–13:45 | Lunch | |
| 13:45–15:00 | **Dry run #2** + pitch lock | **C** finalizes the pitch with team input: problem (30s) → why others fail (20s) → AI's precise role — explicit that the safety verdict comes from DDInter, not the LLM (20s) → live demo (60-90s) → ask/impact (20s). Rehearse the offline cached-JSON fallback as a planned backup, not a panic move |
| 15:00–16:00 | Polish | **C:** visual design pass. **B:** README. **C:** submission form. **All:** clean repo, final commit tag |
| 16:00–17:00 | Final dry run + buffer | One more full run-through, whole team; keep 20-30 min slack for whatever breaks. Print physical one-pager copies to hand judges — your strongest visual prop |

**Day 2 exit criteria:** two dry runs completed successfully, offline fallback tested and works, pitch is under 3 minutes.

---

## 7. Standing risks & how you're covering them

- **Live API flakiness on stage (wifi, rate limits):** cached JSON fallback for your best 2 demo photos, rehearsed as part of the pitch, not a panic move.
- **Gemini misreads Egyptian packaging:** curated brand-name table is your safety net; if vision fails, normalization can still catch a known brand by partial string match.
- **Unrecognized drug (not in DDInter or brand table):** must show "not enough data to confirm — consult your pharmacist" rather than silently dropping it or guessing. Judges will specifically probe this failure path — handle it visibly, don't hide it.
- **Team fatigue on Day 2 afternoon:** the two dry runs are scheduled *before* your final polish hour on purpose — a working-but-ugly demo beats a broken-but-pretty one every time.

---

## 8. Judging framing (from your own proposal — use it verbatim in the pitch)

Emphasize: this doesn't just build another drug-interaction app — it solves *discovery* (getting a real Egyptian patient's medication list into checkable form from physical boxes, which no existing tool does), and it's honest about where AI's job ends and a verified medical database's job begins. That distinction is your strongest differentiator against generic "AI health app" pitches — say it explicitly on stage.
