from services.normalization import (
    _canonical_active,
    _catalog_trade_name,
    normalize_items,
    normalize_key,
    parse_dosage_mg,
)


def test_null_scalar_inputs_are_safe():
    assert normalize_key(None) == ""
    assert parse_dosage_mg(None) is None
    assert _canonical_active(None) == ""
    assert _catalog_trade_name(None) == ""


def test_null_item_fields_are_unresolved_not_crashes():
    result = normalize_items([
        {
            "raw_text": None,
            "drug_name_guess": None,
            "dosage_guess": None,
            "confidence": None,
        }
    ])

    assert result["medications"] == []
    assert result["unresolved"] == [
        {
            "input_name": "",
            "reason": "No match in brand table or RxNorm; LLM review is required.",
        }
    ]


def test_null_or_invalid_items_are_reported():
    result = normalize_items([None, "not-a-dict"])

    assert result["medications"] == []
    assert result["unresolved"] == [
        {"input_name": "", "reason": "Invalid medicine item."},
        {"input_name": "", "reason": "Invalid medicine item."},
    ]
