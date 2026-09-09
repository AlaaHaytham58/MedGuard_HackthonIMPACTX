import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ddinter.importer import CsvSource, ImportValidationError, import_sources, load_manifest
from ddinter.repository import Repository, connect, initialize


class ImporterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.connection = connect(self.root / "test.sqlite")
        self.addCleanup(self.connection.close)
        initialize(self.connection)
        self.repository = Repository(self.connection)

    def source(self, kind, headers, rows, columns, **kwargs):
        path = self.root / f"{kind}.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)
        return CsvSource(kind, path, columns, **kwargs)

    def test_all_entities_and_idempotent_reimport(self):
        # Every name, identifier and statement in this test is synthetic.
        drugs = self.source("drugs", ["label", "external"], [["Drug A", "MOCK-A"], ["Drug B", "MOCK-B"]], {"canonical_name": "label", "ddinter_id": "external"})
        aliases = self.source("aliases", ["owner", "synonym"], [["MOCK-A", "Mock Brand A"]], {"drug": "owner", "alias": "synonym"}, reference="ddinter_id")
        interactions = self.source("interactions", ["left", "right", "level", "text"], [["Mock Brand A", "Drug B", "MAJOR", "Mock only"], ["Drug B", "Drug A", "major", "Mock only"]], {"drug_a": "left", "drug_b": "right", "severity": "level", "description": "text"})
        alternatives = self.source("alternatives", ["owner", "replacement", "text"], [["MOCK-A", "MOCK-B", "Mock only"], ["MOCK-A", "", "Mock textual information"]], {"original_drug": "owner", "alternative_drug": "replacement", "information": "text"}, reference="ddinter_id")
        # Importer orders entity kinds even if manifest order differs.
        sources = [interactions, alternatives, aliases, drugs]
        report = import_sources(self.repository, sources)
        self.assertTrue(report.committed)
        self.assertEqual((report.rows_read, report.drugs_created, report.interactions_created, report.aliases_imported, report.alternatives_imported, report.duplicates_skipped, report.malformed_rows), (7, 2, 1, 1, 2, 1, 0))
        report = import_sources(self.repository, sources)
        self.assertEqual(report.duplicates_skipped, 7)
        self.assertEqual(report.drugs_created + report.interactions_created + report.alternatives_imported, 0)

    def test_skip_malformed_rolls_back_partial_row_and_counts(self):
        source = self.source("interactions", ["a", "b"], [["Drug A", "Drug B"], ["Orphan", ""], ["Self", "Self"], ["Drug B", "Drug A"]], {"drug_a": "a", "drug_b": "b"})
        report = import_sources(self.repository, [source], skip_malformed=True)
        self.assertEqual((report.rows_read, report.drugs_created, report.interactions_created, report.malformed_rows, report.duplicates_skipped), (4, 2, 1, 2, 1))
        self.assertIsNone(self.repository.resolve("Orphan"))
        self.assertIsNone(self.repository.resolve("Self"))
        self.assertEqual(report.errors[0]["line"], 3)

    def test_strict_import_rolls_back_all_files(self):
        source = self.source("interactions", ["a", "b"], [["Drug A", "Drug B"], ["Orphan", ""]], {"drug_a": "a", "drug_b": "b"})
        with self.assertRaises(ImportValidationError) as context:
            import_sources(self.repository, [source])
        self.assertFalse(context.exception.report.committed)
        self.assertEqual(context.exception.report.drugs_created, 0)
        self.assertEqual(self.repository.search("Drug"), [])
        self.assertFalse(self.connection.in_transaction)

    def test_conflicting_reversed_record_is_not_silently_lost(self):
        source = self.source("interactions", ["a", "b", "s"], [["Drug A", "Drug B", "minor"], ["Drug B", "Drug A", "major"]], {"drug_a": "a", "drug_b": "b", "severity": "s"})
        report = import_sources(self.repository, [source], skip_malformed=True)
        self.assertEqual((report.interactions_created, report.malformed_rows, report.duplicates_skipped), (1, 1, 0))

    def test_bad_headers_abort_and_rollback_earlier_file(self):
        drugs = self.source("drugs", ["name"], [["Drug A"]], {"canonical_name": "name"})
        interactions = self.source("interactions", ["wrong"], [["value"]], {"drug_a": "a", "drug_b": "b"})
        with self.assertRaises(ValueError):
            import_sources(self.repository, [drugs, interactions], skip_malformed=True)
        self.assertIsNone(self.repository.resolve("Drug A"))

    def test_wrong_width_is_malformed(self):
        source = self.source("drugs", ["name"], [["Drug A", "extra"]], {"canonical_name": "name"})
        self.assertEqual(import_sources(self.repository, [source], skip_malformed=True).malformed_rows, 1)

    def test_ids_require_preexisting_drugs(self):
        source = self.source("interactions", ["a", "b"], [["MOCK-A", "MOCK-B"]], {"drug_a": "a", "drug_b": "b"}, reference="ddinter_id")
        with self.assertRaises(ImportValidationError):
            import_sources(self.repository, [source])
        self.assertIsNone(self.repository.resolve("MOCK-A"))

    def test_configurable_manifest_paths_and_columns(self):
        path = self.root / "mapping.json"
        path.write_text(json.dumps({"sources": [{"kind": "drugs", "path": "arbitrary.csv", "columns": {"canonical_name": "arbitrary header"}, "delimiter": ";"}]}), encoding="utf-8")
        source = load_manifest(path)[0]
        self.assertEqual(source.path, self.root / "arbitrary.csv")
        self.assertEqual(source.delimiter, ";")
        with self.assertRaises(ValueError):
            CsvSource("drugs", source.path, {"guessed_field": "header"})

    def test_cli_persists_data_and_reports_failure_exit_code(self):
        source = self.source("interactions", ["first", "second"], [["Drug A", "Drug B"]], {"drug_a": "first", "drug_b": "second"})
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"sources": [{"kind": source.kind, "path": source.path.name, "columns": source.columns}]}), encoding="utf-8")
        database = self.root / "cli.sqlite"
        command = [sys.executable, "-m", "ddinter.importer", "--manifest", str(manifest), "--database", str(database)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["interactions_created"], 1)
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["duplicates_skipped"], 1)
        self.source("interactions", ["first", "second"], [["Orphan", ""]], source.columns)
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(result.stdout)["committed"])
        connection = connect(database, readonly=True)
        try:
            self.assertEqual(len(Repository(connection).search("Drug")), 2)
            self.assertIsNone(Repository(connection).resolve("Orphan"))
        finally:
            connection.close()
