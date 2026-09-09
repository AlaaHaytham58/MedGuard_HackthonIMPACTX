# Backend Integration — What A1/A2 Need, and a Guide for B

Two parts: first what **you** (A1/A2) should ask B for, then a section written **to B** that you can paste directly into your team chat.

---

## Part 1 — What you need from B

1. **A yes/no on the contracts** in Part 2 below — mainly whether `/check` needs any field from you that isn't already in `/normalize`'s output.
2. **A real deployed URL, even empty**, as early as possible — don't test only against localhost all night, get a Railway URL you can hit from your own machine.
3. **The exact generic-name format B's DDInter matching expects** (e.g. lowercase, no salt suffix like "fumarate"). This is the #1 silent bug tonight: your `/normalize` says `"Bisoprolol"`, DDInter's table has `"bisoprolol"`, and the match just quietly fails with no error.
4. **Confirmation that `/pipeline` calls your code directly, in-process** — not over HTTP to its own `/extract`/`/normalize` endpoints. This matters, tell them, don't wait to be asked (see Part 2).
5. **Where API keys go** (a shared `.env`, never committed) so nobody accidentally commits a Gemini/RxNorm key to a public repo tonight.

That's it — five short asks, not a negotiation. Send Part 2 to B and you're done.

---

## Part 2 — Guide for B (paste this to them)

### Architecture: one app, one repo — not internal microservices

Structure it as routers calling plain functions, so `/pipeline` never makes an HTTP call to itself:

```
backend/
  main.py                    # FastAPI app, includes routers, sets CORS
  routers/
    extract.py                # wraps A1's function as POST /extract
    normalize.py               # wraps A2's function as POST /normalize
    check.py                     # your POST /check
    pipeline.py                   # your POST /pipeline — orchestrator
  services/
    vision.py                # A1: def extract_drugs(images) -> dict
    normalization.py         # A2: def normalize_items(items) -> dict
    interaction.py           # you: def check_interactions(medications) -> dict
  db/
    ddinter.sqlite
  .env.example
```

`/pipeline` should do this — plain function calls, no self-HTTP:
```python
extracted = extract_drugs(images)
normalized = normalize_items(extracted["items"])
interactions = check_interactions(normalized["medications"])
return combine(normalized, interactions)
```
Why: an HTTP call from `/pipeline` to your own `/extract` adds a network hop and a failure point for no benefit — if it times out live on stage, the whole demo dies for a reason that isn't even real infrastructure. In-process function calls can't do that.

### The contracts to honor (already locked with A1/A2)

**`/extract` output → what `/normalize` receives as `items`:**
```json
{
  "items": [{ "raw_text": "", "drug_name_guess": "", "dosage_guess": "",
              "confidence": 0.0, "bounding_box": [0,0,0,0], "language": "en" }],
  "image_quality_warnings": ["glare", "blur"]
}
```

**`/normalize` output → what `/check` receives as `medications`:**
```json
{
  "medications": [{ "input_name": "", "generic_name": "", "dosage_mg": 0,
                     "rxnorm_id": "", "match_method": "brand_table",
                     "match_confidence": 0.0, "explanation_en": "", "explanation_ar": "" }],
  "unresolved": [{ "input_name": "", "reason": "" }]
}
```

**`/check` output (yours):**
```json
{ "interactions": [{ "drug_a": "", "drug_b": "", "severity": "",
                      "description": "", "source": "ddinter" }] }
```

**`/pipeline` output (yours) — combine the above into what the frontend actually renders.**

### What you specifically need to set up

- **CORS**: `CORSMiddleware` with `allow_origins` including the Vercel URL and `localhost` for dev. Set this up first — forgetting it is a silent, confusing failure discovered late.
- **Secrets**: `.env` (gitignored) + a committed `.env.example` with empty values, so A1/A2 know what keys to request but nothing real leaks.
- **Deploy an empty app to Railway immediately**, before it does anything, so everyone can point at a real URL instead of localhost all night.
- **`GET /health`** — trivial endpoint, lets everyone confirm the deploy is alive without burning Gemini/RxNorm quota.
- **DDInter matching**: decide and document the exact string format you match `generic_name` against (case, whitespace, salt suffixes) — tell A1/A2 this format explicitly, don't leave it implicit.
- **Shared error envelope**, used by every endpoint including yours:
```json
{ "error": true, "code": "SOME_CODE", "message": "human readable", "details": {} }
```

### Testing before A1/A2 are ready

Don't wait on them — build `/check` against a hand-written stub `medications` array matching the contract above, and swap in real input once `/normalize` is live.
