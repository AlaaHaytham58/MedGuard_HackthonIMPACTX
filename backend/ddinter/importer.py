"""CSV import foundation. The real scraper schema is still pending.

TODO(schema mapping): supply a manifest mapping actual CSV headers to the domain
fields below. No CSV filenames, source header names, or medical aliases are assumed.
"""

import argparse
import csv
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .repository import Repository, connect, database_path, initialize

# The only mapping boundary: domain field -> actual CSV header in a JSON manifest.
# Extend here if the delivered files require a new adapter (e.g. list-valued cells).
FIELDS = {
    "drugs": ({"canonical_name"}, {"canonical_name", "ddinter_id"}),
    "aliases": ({"drug", "alias"}, {"drug", "alias"}),
    "interactions": ({"drug_a", "drug_b"}, {
        "drug_a", "drug_b", "severity", "interaction_type", "description",
        "mechanism", "management", "source_reference",
    }),
    "alternatives": ({"original_drug"}, {
        "original_drug", "alternative_drug", "information", "context",
    }),
}


@dataclass
class CsvSource:
    kind: str
    path: Path
    columns: dict[str, str]
    reference: str = "name"
    encoding: str = "utf-8-sig"
    delimiter: str = ","

    def __post_init__(self):
        if self.kind not in FIELDS:
            raise ValueError(f"Unknown source kind: {self.kind}")
        required, allowed = FIELDS[self.kind]
        if not isinstance(self.columns, dict) or not required <= self.columns.keys() <= allowed:
            raise ValueError(f"Invalid domain field mapping for {self.kind}")
        if any(not isinstance(value, str) or not value.strip() for value in self.columns.values()):
            raise ValueError("Mapped CSV header names must be nonempty strings")
        if self.kind == "alternatives" and not ({"alternative_drug", "information"} & self.columns.keys()):
            raise ValueError("Alternatives need a drug or textual information mapping")
        if self.reference not in ("name", "ddinter_id"):
            raise ValueError("reference must be name or ddinter_id")
        if not isinstance(self.delimiter, str) or len(self.delimiter) != 1:
            raise ValueError("CSV delimiter must be one character")


@dataclass
class ImportReport:
    rows_read: int = 0
    drugs_created: int = 0
    interactions_created: int = 0
    aliases_imported: int = 0
    alternatives_imported: int = 0
    duplicates_skipped: int = 0
    malformed_rows: int = 0
    committed: bool = False
    errors: list[dict] = field(default_factory=list)


class ImportValidationError(ValueError):
    def __init__(self, report: ImportReport):
        super().__init__("Malformed CSV row; the import was rolled back")
        self.report = report


def load_manifest(path: Path) -> list[CsvSource]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or set(data) != {"sources"} or not isinstance(data["sources"], list):
        raise ValueError("Manifest must contain only a sources list")
    sources = []
    for item in data["sources"]:
        if not isinstance(item, dict):
            raise ValueError("Each source must be an object")
        item = dict(item)
        item["path"] = path.resolve().parent / item["path"]
        sources.append(CsvSource(**item))
    if not sources:
        raise ValueError("Manifest must contain at least one source")
    return sources


def _drug(repository: Repository, value: str, source: CsvSource, counts: dict) -> int:
    if not value:
        raise ValueError("Empty drug reference")
    if source.reference == "ddinter_id":
        drug = repository.by_ddinter_id(value)
        if drug is None:
            raise ValueError("Unknown DDInter ID; import its canonical drug first")
    else:
        drug, created = repository.ensure_drug(value)
        counts["drugs_created"] = counts.get("drugs_created", 0) + int(created)
    return drug.id


def _import_row(repository: Repository, source: CsvSource, row: dict[str, str]) -> dict[str, int]:
    counts = {}
    if source.kind == "drugs":
        _, created = repository.ensure_drug(row["canonical_name"], row.get("ddinter_id"))
        counts["drugs_created"] = int(created)
    elif source.kind == "aliases":
        drug_id = _drug(repository, row["drug"], source, counts)
        created = repository.add_alias(row["alias"], drug_id)
        counts["aliases_imported"] = int(created)
    elif source.kind == "interactions":
        first = _drug(repository, row["drug_a"], source, counts)
        second = _drug(repository, row["drug_b"], source, counts)
        details = {key: value for key, value in row.items() if key not in ("drug_a", "drug_b")}
        created = repository.add_interaction(first, second, **details)
        counts["interactions_created"] = int(created)
    else:
        original = _drug(repository, row["original_drug"], source, counts)
        alternative = _drug(repository, row["alternative_drug"], source, counts) if row.get("alternative_drug") else None
        created = repository.add_alternative(original, alternative, row.get("information"), row.get("context"))
        counts["alternatives_imported"] = int(created)
    counts["duplicates_skipped"] = int(not created)
    return counts


def import_sources(repository: Repository, sources: list[CsvSource], *, skip_malformed: bool = False) -> ImportReport:
    """Stream files inside one transaction, with row savepoints and indexed reuse.

    Owns the transaction: the supplied connection must have no pending writes.
    Strict by default. In skip mode, invalid rows leave no partial drugs/aliases.
    """
    connection = repository.connection
    if connection.in_transaction:
        raise ValueError("Importer requires a connection without pending writes")
    report = ImportReport()
    order = {kind: index for index, kind in enumerate(FIELDS)}
    try:
        with connection:
            # BEGIN is necessary before SAVEPOINT so RELEASE cannot commit a row.
            connection.execute("BEGIN")
            for source in sorted(sources, key=lambda item: order[item.kind]):
                with source.path.open(newline="", encoding=source.encoding) as handle:
                    reader = csv.DictReader(handle, delimiter=source.delimiter, strict=True)
                    headers = reader.fieldnames
                    if not headers or len(set(headers)) != len(headers) or not set(source.columns.values()) <= set(headers):
                        raise ValueError(f"Missing or duplicate CSV headers in {source.path}")
                    for raw in reader:
                        report.rows_read += 1
                        connection.execute("SAVEPOINT ddinter_row")
                        try:
                            if None in raw or any(value is None for value in raw.values()):
                                raise ValueError("CSV row width does not match its header")
                            row = {key: raw[header].strip() for key, header in source.columns.items()}
                            counts = _import_row(repository, source, row)
                        except (ValueError, sqlite3.IntegrityError) as exc:
                            connection.execute("ROLLBACK TO ddinter_row")
                            report.malformed_rows += 1
                            if len(report.errors) < 20:
                                report.errors.append({"path": str(source.path), "line": reader.line_num, "error": str(exc)})
                            if not skip_malformed:
                                raise ImportValidationError(report) from exc
                        else:
                            for key, count in counts.items():
                                setattr(report, key, getattr(report, key) + count)
                        finally:
                            connection.execute("RELEASE ddinter_row")
        report.committed = True
        return report
    except ImportValidationError:
        report.drugs_created = report.interactions_created = report.aliases_imported = 0
        report.alternatives_imported = report.duplicates_skipped = 0
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--database", type=Path, default=database_path())
    parser.add_argument("--skip-malformed", action="store_true", help="Commit valid rows; report and skip invalid rows")
    args = parser.parse_args()
    connection = None
    try:
        sources = load_manifest(args.manifest)
        args.database.parent.mkdir(parents=True, exist_ok=True)
        connection = connect(args.database)
        initialize(connection)
        report = import_sources(Repository(connection), sources, skip_malformed=args.skip_malformed)
    except ImportValidationError as exc:
        print(json.dumps(asdict(exc.report), indent=2))
        return 1
    except (OSError, ValueError, TypeError, KeyError, csv.Error, sqlite3.Error) as exc:
        print(json.dumps({"committed": False, "error": str(exc)}))
        return 1
    finally:
        if connection is not None:
            connection.close()
    print(json.dumps(asdict(report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
