import sqlite3
import unittest

from ddinter.normalization import normalize_name
from ddinter.repository import Repository, initialize
from ddinter.service import InteractionService, unique_pairs
from tests.support import populate_mock_catalog


class NormalizationTests(unittest.TestCase):
    def test_presentation_and_idempotence(self):
        for value in ("  Drug  A ", "DRUG\tA", "Ｄｒｕｇ\u00a0Ａ"):
            with self.subTest(value=value):
                self.assertEqual(normalize_name(value), "drug a")
                self.assertEqual(normalize_name(normalize_name(value)), "drug a")

    def test_preserves_medically_significant_text(self):
        self.assertEqual(normalize_name("Drug-A Salt 5mg / Drug B"), "drug-a salt 5mg / drug b")
        self.assertEqual(normalize_name(" \t\n"), "")

    def test_unique_pairs(self):
        self.assertEqual(unique_pairs([3, 1, 2, 1]), [(1, 2), (1, 3), (2, 3)])
        self.assertEqual(unique_pairs([1, 1]), [])
        self.assertEqual(len(unique_pairs(list(range(50)))), 1225)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        initialize(self.connection)
        self.addCleanup(self.connection.close)
        self.repository = Repository(self.connection)
        self.a, self.b, self.c, self.d = populate_mock_catalog(self.repository)
        self.service = InteractionService(self.repository)

    def test_resolution_aliases_and_search(self):
        self.assertEqual(self.repository.resolve(" MOCK  BRAND A "), self.a)
        self.assertEqual(self.repository.search("brand"), [self.a])
        self.assertEqual(len(self.repository.search("Drug", 2)), 2)
        self.assertEqual(self.repository.search("%"), [])
        self.assertIsNone(self.repository.resolve("missing"))

    def test_canonical_pair_is_symmetric(self):
        result = self.service.check_pair(self.a, self.b)
        self.assertEqual(result, self.service.check_pair(self.b, self.a))
        self.assertEqual(result.status, "interaction_found")
        self.assertEqual(result.interaction.description, "Synthetic test interaction A-B")
        self.assertIsNone(self.service.check_pair(self.a, self.a))

    def test_three_drugs_three_comparisons_ranked(self):
        result = self.service.check_names(["Drug B", "Drug C", "Drug A"])
        self.assertEqual(result.comparisons, 3)
        self.assertEqual([item.interaction.severity for item in result.interactions], ["major", "moderate", "minor"])
        self.assertEqual(result.status, "complete")

    def test_duplicate_inputs_and_aliases_do_not_add_comparisons(self):
        result = self.service.check_names(["Drug A", "drug a", "Mock Brand A", "Drug B"])
        self.assertEqual(result.comparisons, 1)
        self.assertEqual(len(result.resolutions), 4)
        result = self.service.check_names(["Drug A", "Mock Brand A"])
        self.assertEqual(result.status, "insufficient_distinct_drugs")
        self.assertEqual(result.comparisons, 0)

    def test_unknown_and_missing_record_are_distinct(self):
        result = self.service.check_names(["Drug A", "Drug D", "Missing"])
        self.assertEqual(result.status, "unresolved_drugs")
        self.assertEqual(result.comparisons, 1)
        self.assertEqual(result.no_record_pairs[0].status, "no_record_found")
        self.assertEqual(result.resolutions[-1].status, "unresolved")
        self.assertIn("does not establish", result.notice)
        self.assertEqual(self.service.check_names(["Unknown A", "Unknown B"]).comparisons, 0)

    def test_partial_results_preserve_known_interactions(self):
        result = self.service.check_names(["Drug A", "Drug B", "Missing"])
        self.assertEqual(len(result.interactions), 1)
        self.assertEqual(result.status, "unresolved_drugs")

    def test_unrecognized_severity_is_visible_and_unranked(self):
        self.repository.add_interaction(self.a.id, self.d.id, "unmapped source label")
        result = self.service.check_names(["Drug A", "Drug B", "Drug D"])
        self.assertEqual(result.interactions[-1].interaction.severity, "unmapped source label")
        self.assertIsNone(result.interactions[-1].severity_rank)

    def test_duplicate_reversed_pair_and_conflict(self):
        self.assertFalse(self.repository.add_interaction(self.b.id, self.a.id, "minor", description="Synthetic test interaction A-B"))
        with self.assertRaises(ValueError):
            self.repository.add_interaction(self.b.id, self.a.id, "major")
        with self.assertRaises(ValueError):
            self.repository.add_interaction(self.a.id, self.a.id)

    def test_database_constraints(self):
        for first, second in ((self.b.id, self.a.id), (self.a.id, self.a.id), (self.a.id, self.b.id), (self.a.id, 9999)):
            with self.subTest(pair=(first, second)), self.assertRaises(sqlite3.IntegrityError):
                self.connection.execute("INSERT INTO ddinter_interactions (drug_a_id, drug_b_id, severity) VALUES (?, ?, 'unknown')", (first, second))
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("INSERT INTO ddinter_alternatives (original_drug_id) VALUES (?)", (self.a.id,))

    def test_conflicting_identifiers_and_aliases(self):
        with self.assertRaises(ValueError):
            self.repository.ensure_drug("Drug A", "MOCK-B")
        with self.assertRaises(ValueError):
            self.repository.ensure_drug("Another Name", "MOCK-A")
        with self.assertRaises(ValueError):
            self.repository.add_alias("Drug A", self.b.id)
        with self.assertRaises(ValueError):
            self.repository.add_alias("Mock Brand A", self.b.id)

    def test_alternatives_deduplicate_text_and_linked_records(self):
        self.assertFalse(self.repository.add_alternative(self.a.id, self.d.id, "Synthetic test alternative", "Mock context only"))
        self.assertTrue(self.repository.add_alternative(self.a.id, information="Mock text only"))
        self.assertFalse(self.repository.add_alternative(self.a.id, information="Mock text only"))
        self.assertEqual(len(self.repository.alternatives(self.a.id)), 2)

    def test_service_validation(self):
        for names in (["Drug A"], ["Drug A", " "], ["Drug A", 1], ["Drug A"] * 51):
            with self.subTest(names=names), self.assertRaises(ValueError):
                self.service.check_names(names)
