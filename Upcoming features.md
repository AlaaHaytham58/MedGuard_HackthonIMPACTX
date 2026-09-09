# Upcoming Features

## Pregnancy-safety medication check

**Problem:** Some medications are unsafe (or risky) during pregnancy. This is a
separate risk category from drug-drug interactions (DDInter) and from
duplicate active-ingredient overdose — it depends on *who's taking it*, not
just *what's being combined*.

**Approach (proposed, not yet built):** Same pattern as duplicate
active-ingredient detection — a deterministic, verified lookup, not a
free-form chatbot:

- Key a small curated table on `generic_name` (already computed by
  `/normalize`) against a verified pregnancy-risk category, e.g. the FDA's
  A/B/C/D/X pregnancy categories (simple to encode, well precedented) or
  openFDA data if it has usable coverage.
- If a drug isn't in the table, return an honest "not enough data — ask a
  pharmacist" rather than guessing. Never let this silently pass as "safe."
- If a chat-style explanation is wanted on top, it should only rephrase the
  verified record already looked up — not answer freely from general
  knowledge. Same guardrail as the team's planned grounded-explanation and
  guardrailed-follow-up features: the AI explains, it doesn't invent the
  verdict.

**Why this shape:** A general chatbot risks hallucinating a false "safe"
verdict, which for pregnancy is the failure mode that actually hurts someone.
A lookup table is narrower in coverage but can't do that.

**Open question:** where this plugs in — likely alongside
`duplicate_active_ingredients` in `/check`'s response, gated on the user
having indicated pregnancy status (needs a new input field, not yet part of
any contract).

## Multi-person household tagging

**Problem:** A caregiver often manages medications for more than one person
(e.g. grandmother and grandfather, or a parent and themselves) kept in the
same drawer. Today's pipeline treats every scan as one undifferentiated
medication list, so it can't catch the failure mode caregivers actually
describe: "I think I gave her his pills by mistake."

**Approach (proposed, not yet built):** Add a `person` field to each
medication before duplicate/interaction checks run, then group by person
first:

- Extend the `/normalize` → `/check` contract so each medication entry
  carries an optional `person` tag (assigned by the caregiver in the UI when
  scanning — e.g. "Teta", "Gedo", "myself").
- Run `find_duplicate_active_ingredients` (and the future DDInter check) once
  per person, exactly as today, so existing detection logic is untouched.
- Add a new, distinct check on top: if the *same medication* (by
  `generic_name` + `dosage_mg`) shows up tagged to more than one person, flag
  it as a possible mix-up — someone may have picked up the wrong person's
  dose from the shared drawer.

**Why this shape:** Reuses the existing duplicate/interaction functions
unchanged — `person` is just a grouping key applied before calling them, so
this is near-zero new engineering. It's also a differentiator no generic
interaction checker has: it catches mix-ups *between family members*, not
just chemical interactions between drugs.

**Open question:** how the caregiver assigns a person to each scanned item in
the UI (per-photo vs. per-item tagging), and whether `person` should be a
free-text label or a small pre-declared household-member list.
