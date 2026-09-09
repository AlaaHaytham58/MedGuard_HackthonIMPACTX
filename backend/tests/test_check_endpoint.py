"""Integration coverage for POST /check — the real HTTP contract, not just
the pure duplicate-detection function.

Run with:  cd backend && venv/Scripts/python.exe -m pytest tests/test_check_endpoint.py -v
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_check_flags_duplicate_ingredient_end_to_end():
    payload = {"medications": [
        {"input_name": "Panadol", "generic_name": "paracetamol", "dosage_mg": 500},
        {"input_name": "Adol", "generic_name": "paracetamol", "dosage_mg": 500},
    ]}
    response = client.post("/check", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["interactions"] == []
    assert len(body["duplicate_active_ingredients"]) == 1
    assert body["duplicate_active_ingredients"][0]["active_ingredient"] == "paracetamol"


def test_check_no_duplicates_returns_empty_list():
    payload = {"medications": [
        {"input_name": "Brufen", "generic_name": "ibuprofen", "dosage_mg": 400},
    ]}
    response = client.post("/check", json=payload)
    assert response.status_code == 200
    assert response.json()["duplicate_active_ingredients"] == []


def test_check_empty_medications_list():
    response = client.post("/check", json={"medications": []})
    assert response.status_code == 200
    body = response.json()
    assert body == {"interactions": [], "duplicate_active_ingredients": []}


def test_check_missing_medications_field_defaults_to_empty():
    response = client.post("/check", json={})
    assert response.status_code == 200
    assert response.json()["duplicate_active_ingredients"] == []


def test_check_accepts_medication_with_only_required_style_fields():
    # A hand-written stub, per Backend_Integration_Guide.md's testing advice,
    # won't always populate every optional contract field.
    payload = {"medications": [
        {"generic_name": "paracetamol"},
        {"generic_name": "paracetamol"},
    ]}
    response = client.post("/check", json=payload)
    assert response.status_code == 200
    assert len(response.json()["duplicate_active_ingredients"]) == 1


def test_check_rejects_malformed_medications_type():
    response = client.post("/check", json={"medications": "not-a-list"})
    assert response.status_code == 422


def test_check_rejects_wrong_dosage_type():
    response = client.post("/check", json={
        "medications": [{"generic_name": "paracetamol", "dosage_mg": "not-a-number"}]
    })
    assert response.status_code == 422


def test_check_same_box_scanned_twice_via_http_not_flagged():
    payload = {"medications": [
        {"input_name": "Panadol", "generic_name": "paracetamol", "dosage_mg": 500},
        {"input_name": "Panadol", "generic_name": "paracetamol", "dosage_mg": 500},
    ]}
    response = client.post("/check", json=payload)
    assert response.status_code == 200
    assert response.json()["duplicate_active_ingredients"] == []


def test_check_combo_drug_overlap_via_http():
    payload = {"medications": [
        {"input_name": "Augmentin", "generic_name": "amoxicillin/clavulanate", "dosage_mg": 625},
        {"input_name": "Amoxil", "generic_name": "amoxicillin", "dosage_mg": 500},
    ]}
    response = client.post("/check", json=payload)
    assert response.status_code == 200
    ingredients = {d["active_ingredient"] for d in response.json()["duplicate_active_ingredients"]}
    assert ingredients == {"amoxicillin"}
