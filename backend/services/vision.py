import json
import os
import truststore
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

truststore.inject_into_ssl()

MODEL_NAME = "gemini-2.5-flash"

EXTRACTION_PROMPT = """You are reading photo(s) of medication box(es)/strip(s).
For each distinct medication you can identify, return an entry with:
- raw_text: exact text read
- drug_name_guess: best-guess drug/brand name
- dosage_guess: dosage if visible (e.g., "5mg"), or "" if not visible
- confidence: confidence score 0.0-1.0
- Do NOT split product modifiers or sub-brands into separate items (e.g., read "Panadol Extra" as ONE single drug_name_guess, never split into "Panadol" and "Extra").
- bounding_box: [ymin, xmin, ymax, xmax] on a 0-1000 scale
- language: "en", "ar", or "mixed"

Add image_quality_warnings for issues from ["glare", "blur", "too_dark", "text_too_small"].
If no medication text is readable, return items as an empty list."""


class DrugItem(BaseModel):
    raw_text: str = ""
    drug_name_guess: str = ""
    dosage_guess: str = ""
    confidence: float = 0.0
    bounding_box: list[int] = Field(default_factory=lambda: [0, 0, 0, 0])
    language: str = "en"


class ExtractionResult(BaseModel):
    items: list[DrugItem] = []
    image_quality_warnings: list[str] = []


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
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is missing.")
        _client = genai.Client(api_key=api_key)
    return _client


def extract_drugs(image_bytes_list: list[bytes]) -> dict:
    if os.getenv("MOCK_EXTRACT", "0") == "1":
        return json.loads(json.dumps(_MOCK_RESPONSE))

    client = _get_client()

    parts = [
        types.Part.from_bytes(data=data, mime_type="image/jpeg")
        for data in image_bytes_list
    ]
    parts.append(EXTRACTION_PROMPT)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionResult,
        ),
    )

    if response.parsed:
        return response.parsed.model_dump()

    return json.loads(response.text)