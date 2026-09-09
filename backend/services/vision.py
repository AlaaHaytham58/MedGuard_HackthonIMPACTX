import json
import os
import re

import truststore

truststore.inject_into_ssl()

from google import genai

MODEL_NAME = "gemini-3.6-flash"

EXTRACTION_PROMPT = """You are reading photo(s) of medication box(es)/strip(s).
For each distinct medication you can identify, return an entry with:
- the exact text you read (raw_text)
- your best-guess drug/brand name (drug_name_guess)
- dosage if visible (dosage_guess), e.g. "5mg", or "" if not visible
- a confidence score 0-1 for how sure you are this is a real, correctly-read drug name
- a bounding box [ymin, xmin, ymax, xmax] on a 0-1000 scale locating that text in the image
- the language of the text: "en", "ar", or "mixed"

Also add image_quality_warnings: a list of strings from ["glare", "blur", "too_dark", "text_too_small"]
for any problems that made reading harder. Empty list if the photo was clear.

If you see no readable medication text at all, return items as an empty list — do not guess.

Return ONLY valid JSON, no prose, no markdown fences, matching exactly this shape:
{
  "items": [
    {
      "raw_text": "",
      "drug_name_guess": "",
      "dosage_guess": "",
      "confidence": 0.0,
      "bounding_box": [0, 0, 0, 0],
      "language": "en"
    }
  ],
  "image_quality_warnings": []
}
"""

_client = None

_MOCK_RESPONSE = {
    "items": [
        {
            "raw_text": "Brufen 400mg",
            "drug_name_guess": "Brufen",
            "dosage_guess": "400mg",
            "confidence": 0.95,
            "bounding_box": [120, 80, 260, 620],
            "language": "en",
        },
        {
            "raw_text": "Concor 5mg",
            "drug_name_guess": "Concor",
            "dosage_guess": "5mg",
            "confidence": 0.93,
            "bounding_box": [340, 80, 480, 620],
            "language": "en",
        },
    ],
    "image_quality_warnings": [],
}


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ["GEMINI_API_KEY"]
        _client = genai.Client(api_key=api_key)
    return _client


def _parse_json_block(text: str) -> dict:
    """Gemini sometimes wraps JSON in ```json fences even when told not to — strip defensively."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {text[:200]!r}")
    return json.loads(match.group(0))


def extract_drugs(image_bytes_list: list[bytes]) -> dict:
    """Takes raw image bytes (one or more photos), returns the /extract contract dict.

    This is a plain function on purpose (no FastAPI/HTTP here) so it can be called
    directly in-process later by the /pipeline orchestrator, per the backend guide.
    """
    if os.getenv("MOCK_EXTRACT") == "1":
        return json.loads(json.dumps(_MOCK_RESPONSE))  # deep copy, caller may mutate

    client = _get_client()

    parts = [
        genai.types.Part.from_bytes(data=data, mime_type="image/jpeg")
        for data in image_bytes_list
    ]
    parts.append(EXTRACTION_PROMPT)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=parts,
    )

    data = _parse_json_block(response.text)
    data.setdefault("items", [])
    data.setdefault("image_quality_warnings", [])

    for item in data["items"]:
        item.setdefault("raw_text", "")
        item.setdefault("drug_name_guess", "")
        item.setdefault("dosage_guess", "")
        item.setdefault("confidence", 0.0)
        item.setdefault("bounding_box", [0, 0, 0, 0])
        item.setdefault("language", "en")

    return data
