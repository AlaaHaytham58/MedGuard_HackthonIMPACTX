"""Exhaustive scenario coverage for services/duplicates.py.

Run with:  cd backend && venv/Scripts/python.exe -m pytest tests/test_duplicates.py -v
"""

import pytest

from services.duplicates import find_duplicate_active_ingredients


def med(input_name="", generic_name="", dosage_mg=None):
    return {"input_name": input_name, "generic_name": generic_name, "dosage_mg": dosage_mg}


def ingredients(result):
    return {d["active_ingredient"] for d in result}


# ---------------------------------------------------------------------------
# Basic detection
# ---------------------------------------------------------------------------

class TestBasicDetection:
    def test_two_brands_same_ingredient_flagged(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 500),
        ])
        assert ingredients(result) == {"paracetamol"}
        names = {m["input_name"] for m in result[0]["medications"]}
        assert names == {"Panadol", "Adol"}

    def test_three_brands_same_ingredient_flagged(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 500),
            med("Fevadol", "paracetamol", 125),
        ])
        assert len(result) == 1
        assert len(result[0]["medications"]) == 3

    def test_no_duplicates_when_all_different(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Brufen", "ibuprofen", 400),
            med("Concor", "bisoprolol", 5),
        ])
        assert result == []

    def test_single_medication_never_flagged(self):
        result = find_duplicate_active_ingredients([med("Panadol", "paracetamol", 500)])
        assert result == []

    def test_empty_medication_list(self):
        assert find_duplicate_active_ingredients([]) == []

    def test_two_of_three_share_ingredient(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 500),
            med("Brufen", "ibuprofen", 400),
        ])
        assert ingredients(result) == {"paracetamol"}


# ---------------------------------------------------------------------------
# Ingredient-string normalization
# ---------------------------------------------------------------------------

class TestNormalization:
    def test_case_insensitive_match(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "PARACETAMOL", 500),
            med("Fevadol", "Paracetamol", 500),
        ])
        assert ingredients(result) == {"paracetamol"}
        assert len(result[0]["medications"]) == 3

    def test_surrounding_whitespace_ignored(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "  paracetamol  ", 500),
        ])
        assert ingredients(result) == {"paracetamol"}

    def test_internal_whitespace_collapsed(self):
        result = find_duplicate_active_ingredients([
            med("A", "paracetamol", 500),
            med("B", "para cetamol", 500),  # pathological OCR-ish spacing, still distinct token
        ])
        # These are legitimately different tokens post-normalization, not a false match.
        assert result == []

    @pytest.mark.parametrize("suffix", [
        "hydrochloride", "hcl", "sodium", "potassium", "calcium",
        "sulfate", "sulphate", "fumarate", "maleate", "tartrate", "bitartrate",
        "citrate", "besylate", "mesylate", "succinate", "phosphate", "acetate",
        "dihydrate", "monohydrate", "trihydrate", "anhydrous",
    ])
    def test_salt_suffix_stripped_for_every_known_suffix(self, suffix):
        result = find_duplicate_active_ingredients([
            med("BrandBare", "metformin", 500),
            med("BrandSalt", f"metformin {suffix}", 500),
        ])
        assert ingredients(result) == {"metformin"}, f"failed for suffix={suffix!r}"

    def test_multiple_stacked_salt_suffixes_stripped(self):
        result = find_duplicate_active_ingredients([
            med("A", "metformin", 500),
            med("B", "metformin hydrochloride dihydrate", 500),
        ])
        assert ingredients(result) == {"metformin"}

    def test_parenthetical_qualifier_stripped(self):
        result = find_duplicate_active_ingredients([
            med("A", "amoxicillin (as trihydrate)", 500),
            med("B", "amoxicillin", 500),
        ])
        assert ingredients(result) == {"amoxicillin"}

    def test_empty_generic_name_skipped_not_crashed(self):
        result = find_duplicate_active_ingredients([
            med("Unresolved", "", 0),
            med("Panadol", "paracetamol", 500),
        ])
        assert result == []

    def test_missing_generic_name_key_entirely(self):
        # /normalize's contract guarantees the key, but don't crash if a caller omits it.
        result = find_duplicate_active_ingredients([
            {"input_name": "Unresolved"},
            {"input_name": "Panadol", "generic_name": "paracetamol"},
        ])
        assert result == []

    def test_missing_input_name_key_entirely(self):
        result = find_duplicate_active_ingredients([
            {"generic_name": "paracetamol"},
            {"generic_name": "paracetamol"},
        ])
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Combination drugs (multiple active ingredients per medication)
# ---------------------------------------------------------------------------

class TestComboDrugs:
    @pytest.mark.parametrize("separator", ["/", "+", ";", ",", "&", " and ", " with "])
    def test_every_supported_separator_splits_ingredients(self, separator):
        generic = f"amoxicillin{separator}clavulanate"
        result = find_duplicate_active_ingredients([
            med("Augmentin", generic, 625),
            med("Amoxil", "amoxicillin", 500),
        ])
        assert "amoxicillin" in ingredients(result), f"failed for separator={separator!r}"

    def test_combo_overlaps_single_ingredient_drug(self):
        result = find_duplicate_active_ingredients([
            med("Augmentin", "amoxicillin/clavulanate", 625),
            med("Amoxil", "amoxicillin", 500),
        ])
        assert ingredients(result) == {"amoxicillin"}
        names = {m["input_name"] for m in result[0]["medications"]}
        assert names == {"Augmentin", "Amoxil"}

    def test_two_combos_partial_overlap_flags_only_shared_ingredient(self):
        result = find_duplicate_active_ingredients([
            med("Panadol Extra", "paracetamol/caffeine", 500),
            med("Cetal Plus", "paracetamol/codeine", 500),
        ])
        assert ingredients(result) == {"paracetamol"}

    def test_three_ingredient_combo_only_shared_one_flagged(self):
        result = find_duplicate_active_ingredients([
            med("TriplePain", "paracetamol/caffeine/codeine", 500),
            med("PlainCaff", "caffeine", 65),
        ])
        assert ingredients(result) == {"caffeine"}

    def test_ingredient_order_within_combo_does_not_matter(self):
        result = find_duplicate_active_ingredients([
            med("Augmentin", "amoxicillin/clavulanate", 625),
            med("GenericCombo", "clavulanate/amoxicillin", 625),
        ])
        assert ingredients(result) == {"amoxicillin", "clavulanate"}
        for group in result:
            assert len(group["medications"]) == 2

    def test_repeated_ingredient_within_single_medication_not_self_counted(self):
        # A malformed generic_name repeating the same ingredient must not, by itself,
        # look like 2 distinct products.
        result = find_duplicate_active_ingredients([med("Weird", "paracetamol/paracetamol", 500)])
        assert result == []

    def test_no_false_positive_between_unrelated_combo_ingredients(self):
        result = find_duplicate_active_ingredients([
            med("Panadol Extra", "paracetamol/caffeine", 500),
            med("Cetal Plus", "paracetamol/codeine", 500),
        ])
        assert "caffeine" not in ingredients(result)
        assert "codeine" not in ingredients(result)


# ---------------------------------------------------------------------------
# Same-product dedupe (the "photographed the same box twice" false positive)
# ---------------------------------------------------------------------------

class TestProductDedupe:
    def test_same_box_scanned_twice_alone_not_flagged(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Panadol", "paracetamol", 500),
        ])
        assert result == []

    def test_same_box_scanned_twice_case_insensitive_brand_match(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("panadol", "paracetamol", 500),
        ])
        assert result == []

    def test_same_box_twice_plus_real_duplicate_only_counts_distinct_products(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 500),
        ])
        assert len(result) == 1
        names = [m["input_name"] for m in result[0]["medications"]]
        assert names == ["Panadol", "Adol"]

    def test_entries_missing_input_name_never_collapsed_together(self):
        result = find_duplicate_active_ingredients([
            med("", "ibuprofen", 400),
            med("", "ibuprofen", 200),
        ])
        assert len(result) == 1
        assert len(result[0]["medications"]) == 2


# ---------------------------------------------------------------------------
# Output shape and message formatting
# ---------------------------------------------------------------------------

class TestOutputShape:
    def test_severity_is_always_high(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 500),
        ])
        assert result[0]["severity"] == "high"

    def test_results_sorted_alphabetically_by_ingredient(self):
        result = find_duplicate_active_ingredients([
            med("A1", "paracetamol", 500), med("A2", "paracetamol", 500),
            med("B1", "amoxicillin", 500), med("B2", "amoxicillin", 500),
            med("C1", "ibuprofen", 500), med("C2", "ibuprofen", 500),
        ])
        assert [d["active_ingredient"] for d in result] == ["amoxicillin", "ibuprofen", "paracetamol"]

    def test_medication_entries_preserve_dosage_and_generic_name(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 125),
        ])
        by_name = {m["input_name"]: m for m in result[0]["medications"]}
        assert by_name["Panadol"]["dosage_mg"] == 500
        assert by_name["Adol"]["dosage_mg"] == 125

    def test_message_join_two_names(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 500),
        ])
        assert "Panadol and Adol" in result[0]["message"]

    def test_message_join_three_names(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 500),
            med("Fevadol", "paracetamol", 500),
        ])
        assert "Panadol, Adol, and Fevadol" in result[0]["message"]

    def test_message_join_many_names(self):
        meds = [med(f"Brand{i}", "paracetamol", 500) for i in range(5)]
        result = find_duplicate_active_ingredients(meds)
        msg = result[0]["message"]
        assert "Brand0, Brand1, Brand2, Brand3, and Brand4" in msg

    def test_message_falls_back_to_generic_and_dosage_when_no_brand(self):
        result = find_duplicate_active_ingredients([
            med("", "ibuprofen", 400),
            med("", "ibuprofen", 200),
        ])
        assert "ibuprofen (400mg)" in result[0]["message"]
        assert "ibuprofen (200mg)" in result[0]["message"]


# ---------------------------------------------------------------------------
# Realistic Egyptian brand-table scenarios (from the hackathon plan doc)
# ---------------------------------------------------------------------------

class TestRealisticScenarios:
    def test_panadol_adol_fevadol_paracetamol_overdose(self):
        result = find_duplicate_active_ingredients([
            med("Panadol", "paracetamol", 500),
            med("Adol", "paracetamol", 500),
            med("Fevadol", "paracetamol", 125),
            med("Brufen", "ibuprofen", 400),
            med("Concor", "bisoprolol", 5),
        ])
        assert ingredients(result) == {"paracetamol"}

    def test_full_chronic_disease_cabinet_no_false_positives(self):
        # A plausible elderly patient's real drawer: distinct drugs, no overlaps.
        result = find_duplicate_active_ingredients([
            med("Concor", "bisoprolol", 5),
            med("Glucophage", "metformin", 500),
            med("Cataflam", "diclofenac", 50),
            med("Augmentin", "amoxicillin/clavulanate", 625),
        ])
        assert result == []

    def test_glucophage_and_generic_metformin_flagged(self):
        result = find_duplicate_active_ingredients([
            med("Glucophage", "metformin hydrochloride", 500),
            med("Cidophage", "metformin", 850),
        ])
        assert ingredients(result) == {"metformin"}
