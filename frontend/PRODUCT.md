# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Backend: Python + FastAPI. Frontend: React (Vite). DDInter 2.0 bulk interaction data loaded into a local SQLite file at build time (no live scraping/querying). Deploy: frontend to Vercel, backend to Railway. Locked in the team's own hackathon execution plan (`MedGuard_Hackathon_Extreme_Plan.md`) specifically to avoid relitigating the stack mid-hackathon.

## Users

Primary: Egyptian patients and their caregivers managing multiple medications — especially elderly patients and chronic-disease patients on polypharmacy — most comfortable in Arabic, who need to know whether the medications they're taking together are safe. Situation: they have physical medication boxes/strips in hand, labeled with Egyptian brand names rather than generic drug names, and no easy way to check interactions themselves. Job: photograph their medications and get a plain-language, trustworthy answer about dangerous interactions or duplicates, without needing to already know unfamiliar generic names.

Secondary (current milestone only): judges evaluating the live prototype at IMPACT 2026, Healthcare Track.

## Product Purpose

MedGuard turns physical medication packaging into a checkable drug-interaction report. It solves the "discovery" problem specific to Egyptian patients: getting a real patient's actual medication list — as Egyptian brand names on physical boxes — into a form that can be checked against a verified interaction database. No existing interaction-checker tool handles this; they all assume the user already knows generic drug names. Success is a patient or caregiver photographing 2-4 medication packages and receiving an accurate, plain-language, printable summary that flags duplicate or interacting drugs, with any unrecognized drug surfaced honestly rather than silently dropped.

## Positioning

MedGuard's differentiator is the explicit separation of roles: AI (Gemini Vision + LLM) only extracts and normalizes drug names from photos into generic identifiers; the safety verdict itself always comes from a deterministic, verified medical database (DDInter 2.0, with openFDA as fallback) — never from the LLM's judgment. This can't be truthfully copied by a tool that either (a) requires the user to already know generic names, or (b) lets an LLM adjudicate safety itself instead of a verified database.

## Operating Context

- Real-world use: a patient or caregiver at home, often before a doctor visit or pharmacist conversation, holding 2-4 physical medication boxes/strips with Egyptian brand names — packaging that may be worn, glare-affected, or partially in Arabic.
- Current milestone: IMPACT 2026, Healthcare Track, judged live on stage; must survive a venue-wifi outage via a cached-response offline fallback for the demo's best photo set.
- Output is consumed both on-screen and as a printed physical one-pager — the team's strongest visual prop for judges, and plausibly something a caregiver could bring to a doctor.

## Capabilities and Constraints

Current (hackathon) milestone — MUST: upload 2-4 photos → Gemini Vision extraction → RxNorm/LLM normalization to generics → DDInter 2.0 interaction/duplicate check → plain-language, printable one-page summary. UI is English-only for this build.
SHOULD: openFDA fallback when DDInter has no match; graceful handling of unrecognized Egyptian brand names.
Explicitly CUT for this milestone (build-scope only, not a rejection of real-world need): multi-language UI, user accounts, history/save, native mobile app wrapper (responsive web only), decorative animation.
Non-negotiable failure behavior: an unrecognized drug must show "not enough data to confirm — consult your pharmacist," never crash or silently drop it — this failure path will specifically be probed by judges and real users alike.

Real-world target (deferred past current milestone): bilingual UI — Arabic for navigation, labels, and plain-language explanations, with English retained for drug and medical terminology (matching common Egyptian healthcare convention). English-only is a build-scope shortcut, not the product's real target language.

## Brand Commitments

Name: MedGuard. No logo, color system, or other visual identity assets confirmed yet.

## Evidence on Hand

No real demo photos captured yet at time of writing (the plan calls for the team to shoot 8-10 real medication photos during prep, doubling as test set and demo material) — do not fabricate sample packaging, brand names, or interaction results in any design or copy; use only real captured photos and real DDInter/RxNorm/openFDA responses once available. No user testimonials, case studies, or press exist; this is a pre-launch hackathon prototype.

## Product Principles

1. The AI never renders the safety verdict — only a verified deterministic database (DDInter 2.0 / openFDA) does — and this boundary is stated explicitly to the user, not left implicit.
2. Discovery over lookup: assume the user knows their medications only by physical packaging or brand name, never by generic name.
3. Fail visibly, never silently: an unrecognized drug or failed match is surfaced as a stated limitation ("consult your pharmacist"), not dropped or guessed at.
4. Plain language over clinical language: every output must be understandable by a non-technical, potentially elderly caregiver.
5. Real-world reliability over demo polish: an offline-safe, honest fallback path is a product requirement, not just a hackathon safety net.

## Accessibility & Inclusion

Informal bar for now: plain, non-technical language; legible, uncluttered layout suited to elderly and non-technical caregivers. No formal standard (e.g. WCAG) targeted at this time; revisit if the product moves toward real-world deployment.
