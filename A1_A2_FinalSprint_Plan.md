# MedGuard — A1 + A2 Final Sprint Plan
**T-minus ~14 hours to submission (8:00 AM deadline)**

> Time assumption: written at 17:35 Cairo time (UTC+3) on 2026-09-09, targeting 08:00 the next morning. If your actual local time is different, don't re-derive the plan — just slide every hour block below by the difference.

This replaces the "2 prep days + 2 hackathon days" version of the plan. You don't have that anymore. This is scoped tightly to **A1 (Vision Extraction)** and **A2 (Normalization)** — the two AI-heavy roles — with everything else (B = interaction engine, C = frontend/demo) treated as parallel tracks you sync with, not things you own.

---

## 0. Reality check — read this before touching code

- You will **not** get every stretch feature in this doc. That's fine. It's ordered so that cutting from the bottom still leaves you with something impressive.
- The single biggest risk tonight isn't AI quality — it's **A1 and A2 output formats not matching what the other person's code expects at 3 AM**. Section 1 fixes that. Do it first, even before writing a line of extraction code.
- Judges at a healthcare hackathon see 20 "upload a photo, LLM says something" demos. What makes yours look like *real* engineering instead of a ChatGPT wrapper is: **(1)** you can show *where* in the image the AI read each drug from, and **(2)** the explanation is grounded in your actual interaction data, not the LLM freelancing. Both are in Section 2, and both are achievable tonight.

---

## 1. Lock the JSON contract now (15 min, do this together before splitting up)

A1's `/extract` output is A2's `/normalize` input. Agree on this literally right now, out loud, before either of you writes extraction/normalization logic. Paste both of these into your shared doc/Slack.

**A1 → A2 contract (`/extract` response):**
```json
{
  "items": [
    {
      "raw_text": "Concor 5mg",
      "drug_name_guess": "Concor",
      "dosage_guess": "5mg",
      "confidence": 0.92,
      "bounding_box": [ymin, xmin, ymax, xmax],
      "language": "en"
    }
  ],
  "image_quality_warnings": ["glare", "blur"]
}
```

**A2 → B contract (`/normalize` response) — B will consume this, so agree with B too if you can grab 2 minutes:**
```json
{
  "medications": [
    {
      "input_name": "Concor 5mg",
      "generic_name": "bisoprolol",
      "dosage_mg": 5,
      "rxnorm_id": "19484",
      "match_method": "brand_table",
      "match_confidence": 0.95,
      "explanation_en": "...",
      "explanation_ar": "..."
    }
  ],
  "unresolved": [
    { "input_name": "Xyzobrand", "reason": "no match in brand table, RxNorm, or LLM fallback" }
  ]
}
```

**Why this matters:** if B or C aren't ready with `/check` yet, A2 should build against a **hand-written stub JSON** matching what B promised to return, so A2 is never blocked waiting on B. Same logic for A1/A2 — don't wait on each other, build against the contract above and swap in real code later.

---

## 2. The two features that make this "impressive AI," not "simple"

Everything else in this plan is standard pipeline work. These two are the ones worth spending real hours on, because they're highly demo-visible and directly support your team's differentiator ("AI does discovery, a verified database does the safety verdict" — keep saying that line).

### Feature 1 (A1 owns): Visual grounding — show the AI's work

Instead of just returning drug names as text, have Gemini return **where on the image it read each one**, and render that as a bounding-box overlay on the photo in the results screen. This is the single highest wow-to-effort feature available to you — judges visibly see "the AI actually looked at my photo," which most competing demos won't show.

Gemini Vision supports returning normalized bounding boxes (0–1000 scale, `[ymin, xmin, ymax, xmax]`) when you ask for them explicitly in the prompt. Concrete prompt:

```
You are reading a photo of medication box(es)/strip(s). For each distinct
medication you can identify, return an entry with:
- the exact text you read (raw_text)
- your best-guess drug/brand name (drug_name_guess)
- dosage if visible (dosage_guess)
- a confidence score 0-1 for how sure you are this is a real, correctly-read drug name
- a bounding box [ymin, xmin, ymax, xmax] on a 0-1000 scale locating that text in the image
- the language of the text: "en", "ar", or "mixed"

Also flag image_quality_warnings if the photo has glare, blur, or is too dark to read reliably.

Return ONLY valid JSON matching this schema, no prose:
{ "items": [...], "image_quality_warnings": [...] }
```

Implementation notes:
- If combining structured JSON mode (`response_schema`) with bounding boxes proves flaky in testing, split into two calls: one strict-schema call for the drug list, one prompt-only call for boxes keyed by `raw_text`. Don't burn more than 30 min fighting this — a version without boxes but with confidence scores is still fine, see cut order in Section 6.
- Hand B/C the box coordinates in the contract above (already included) so C can draw a `<div>` overlay on the `<img>` — that's a frontend task, not yours, just make sure the numbers are correct and documented as 0–1000 normalized, not pixels.

### Feature 2 (A2 owns): Grounded bilingual explanation + guardrailed follow-up

Two parts, both cheap once the first is built:

**(a) Bilingual, grounded plain-language explanation.** Once B's `/check` returns a DDInter match (severity + description), have the LLM turn that into a caregiver-friendly explanation in **both English and Arabic** — this is a strong localization point for Egyptian judges and directly serves your target user (elderly caregiver, not a pharmacist). Critical: the LLM must be **grounded** — it explains the DDInter record, it does not invent new medical claims.

```
You are explaining a drug interaction to a non-medical caregiver in Egypt.
You are given a verified interaction record from a medical database. Do not
add any medical claims beyond what is given. If the record doesn't specify
something, say so rather than guessing.

Interaction record:
  Drug A: {generic_a}
  Drug B: {generic_b}
  Severity: {severity}
  Description: {ddinter_description}

Write two short paragraphs (3-4 sentences each), one in plain English, one
in Modern Standard Arabic, explaining:
  1. what the risk is, in plain non-technical language
  2. what the caregiver should do (e.g. "ask a pharmacist before combining these")
Do not diagnose. Do not recommend stopping medication. End both with a
reminder that this is not a substitute for professional medical advice.

Return JSON: { "explanation_en": "...", "explanation_ar": "..." }
```

**(b) Guardrailed "Ask MedGuard" follow-up (stretch, only if (a) is done with time to spare).** A tiny chat box under the results where the caregiver can ask "why exactly is this dangerous?" — but the system prompt restricts the LLM to only the DDInter record + normalized medication list already on screen, explicitly forbidding new diagnoses or drug suggestions. This demos extremely well ("watch, I can ask it a follow-up") and is low-risk because the guardrail keeps it from hallucinating on stage. If you build this, rehearse 2 fixed questions to ask live — don't improvise on stage.

**(c) Fuzzy matching for near-misses (stretch, A2).** OCR from A1 will sometimes be slightly off ("Concar" instead of "Concor"). Use `rapidfuzz` (one `pip install`, no API cost) to fuzzy-match against your brand table before falling back to the LLM — cheap, fast, and turns a chunk of "unresolved" items into confident matches. Add `match_method: "fuzzy_match"` to the contract, already accounted for above.

---

## 3. Hour-by-hour — A1 (Vision Extraction)

| Block | Task |
|---|---|
| **H0:00–0:15** | Joint: lock the contract (Section 1) with A2. |
| **H0:15–2:15** | Get raw Gemini Vision extraction working on your real demo photos (reuse the ones from prep if you have them; shoot more now if not — you need at least 5-6 real boxes/strips, varied lighting). Plain text/name extraction first, no JSON structure yet. Get it *working*, not pretty. |
| **H2:15–4:15** | Upgrade to the structured JSON contract from Section 1: `drug_name_guess`, `dosage_guess`, `confidence`, `language`, `image_quality_warnings`. Test against 5+ photos, fix parsing (LLMs sometimes wrap JSON in markdown fences — strip that defensively). |
| **H4:15–4:30** | Mini-sync with A2: send them 2-3 real `/extract` outputs, confirm their code parses your JSON with no surprises. |
| **H4:30–6:30** | Add bounding boxes (Feature 1). If it's fighting you past ~45 min, drop boxes and keep confidence-only — don't let this eat your whole night. |
| **H6:30–7:00** | **Full pipeline sync** with A2 + B + C: real photo → extract → normalize → check → rendered on screen, even if ugly. This is the most important checkpoint tonight — protect it. |
| **H7:00–9:00** | Bugfix block from the integration test — always takes longer than you think. |
| **H9:00–10:30** | Harden edge cases: retry logic on Gemini timeouts/rate limits, glare/blur detection warnings actually surfaced in the UI (coordinate with C), test against any new photos taken tonight. |
| **H10:30–11:30** | Stretch only if ahead: OCR fallback (Tesseract) if Gemini fails entirely — nice resilience story for judges. Otherwise, skip straight to dry run. |
| **H11:30–12:30** | Whole-team dry run. Capture cached JSON responses for your 2 best demo photos as the offline fallback. |
| **H12:30–13:15** | Bugfix only — feature freeze. |
| **H13:15–14:00** | Final commit, README, submission, buffer. |

---

## 4. Hour-by-hour — A2 (Normalization)

| Block | Task |
|---|---|
| **H0:00–0:15** | Joint: lock the contract (Section 1) with A1. |
| **H0:15–2:15** | Build/finish the Egyptian brand→generic table (30-40 entries — prioritize what's actually in your demo photos plus common chronic-disease drugs: Concor→bisoprolol, Glucophage→metformin, Panadol→paracetamol, Brufen→ibuprofen, Cataflam→diclofenac, Augmentin→amoxicillin/clavulanate, etc). Wire up RxNorm API for anything not in the table. |
| **H2:15–4:15** | LLM fallback for anything RxNorm + brand table both miss. Add `match_method` and `match_confidence` to every output per the contract. Build against a **stub** `/extract` response first if A1 isn't ready yet — don't idle. |
| **H4:15–4:30** | Mini-sync with A1: confirm you're correctly parsing their real `/extract` JSON. |
| **H4:30–6:30** | Feature 2(a): bilingual grounded explanation generator. Build against a **stub** DDInter record from B if `/check` isn't live yet (agree on B's response shape in 2 min if you can). |
| **H6:30–7:00** | **Full pipeline sync** with A1 + B + C (same checkpoint as A1's row above). |
| **H7:00–9:00** | Bugfix block from integration. |
| **H9:00–10:30** | Polish Arabic wording specifically for an elderly, non-medical reader — read it out loud, cut jargon. Tighten fuzzy-match thresholds so near-miss OCR doesn't produce false "unresolved" results. |
| **H10:30–11:30** | Stretch only if ahead: Feature 2(b) guardrailed follow-up chat, or 2(c) rapidfuzz matching if not already in from H2:15 block. Pick ONE, not both. |
| **H11:30–12:30** | Whole-team dry run. |
| **H12:30–13:15** | Bugfix only — feature freeze. |
| **H13:15–14:00** | Final commit, README, submission, buffer. |

---

## 5. Sync discipline tonight

- **Don't wait on each other or on B/C.** Every handoff above has a stub option — use it. The 30-min mini-sync at H4:15 is where you swap real output for stub output.
- **The H6:30 full-pipeline sync is sacred.** This is the same "most important milestone" moment your original plan flagged — a rough end-to-end chain, even ugly, de-risks everything after it. If it's not working by H7:00, that becomes the top priority over any stretch feature.
- Stand up every 2 hours with the whole team, 5 minutes: what's done, what's blocked, what's next. Don't skip this even at 2 AM — it's what catches contract drift before it becomes a 3 AM debugging session.

---

## 6. Cut order — if you fall behind, cut in exactly this order

1. Feature 2(b) — guardrailed follow-up chat
2. Feature 2(c) — fuzzy matching (fall back to exact-match + LLM fallback only)
3. Bounding box overlay (keep confidence score, drop the visual box)
4. Arabic explanation (English-only explanation is still fine)
5. **Never cut:** the core chain (photo → names → generics → interaction flag → plain summary) and the offline cached-JSON fallback. Those are what actually get judged; everything above is what makes it impressive on top of working.

---

## 7. What to actually say about these features on stage

Keep it to one sentence each, said plainly, not oversold:

- *"You can see exactly which part of the photo the AI read each medication from — this isn't a black box guess."*
- *"The explanation you're reading is generated in both English and Arabic, but it's grounded strictly in a verified interaction database — the AI explains the finding, it doesn't invent the medical verdict."*

That second line also reinforces your team's core differentiator from the original pitch — say it explicitly, judges remember the team that's honest about where the AI's job stops.
