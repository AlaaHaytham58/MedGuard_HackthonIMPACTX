import os
import sqlite3
from pathlib import Path

from .models import AlternativeDrug, Drug, DrugInteraction
from .normalization import normalize_name

# Independent, namespaced tables to avoid collisions with the team's future backend.
SCHEMA = """
CREATE TABLE IF NOT EXISTS ddinter_drugs (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL UNIQUE CHECK (length(normalized_name) > 0),
    ddinter_id TEXT UNIQUE,
    drugbank_id TEXT
);
CREATE TABLE IF NOT EXISTS ddinter_aliases (
    id INTEGER PRIMARY KEY,
    alias TEXT NOT NULL,
    normalized_name TEXT NOT NULL UNIQUE CHECK (length(normalized_name) > 0),
    drug_id INTEGER NOT NULL REFERENCES ddinter_drugs(id)
);
CREATE TABLE IF NOT EXISTS ddinter_interactions (
    id INTEGER PRIMARY KEY,
    drug_a_id INTEGER NOT NULL REFERENCES ddinter_drugs(id),
    drug_b_id INTEGER NOT NULL REFERENCES ddinter_drugs(id),
    severity TEXT NOT NULL,
    interaction_type TEXT,
    description TEXT,
    mechanism TEXT,
    management TEXT,
    source_reference TEXT,
    pair_id INTEGER UNIQUE,
    definition_id TEXT,
    pair_key TEXT,
    detail_url TEXT,
    interaction_text TEXT,
    detail_available INTEGER NOT NULL DEFAULT 0,
    CHECK (drug_a_id < drug_b_id)
);
CREATE TABLE IF NOT EXISTS ddinter_definitions (
    definition_id TEXT PRIMARY KEY,
    severity TEXT NOT NULL,
    mechanism TEXT NOT NULL,
    description TEXT,
    source_url TEXT NOT NULL,
    scraped_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ddinter_pair_details (
    pair_id INTEGER PRIMARY KEY REFERENCES ddinter_interactions(pair_id),
    interaction_text TEXT,
    management TEXT,
    references_text TEXT,
    alternative_a TEXT,
    alternative_b TEXT,
    source_url TEXT NOT NULL,
    scraped_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ddinter_references (
    pair_id INTEGER NOT NULL REFERENCES ddinter_interactions(pair_id),
    reference_number INTEGER NOT NULL,
    reference_text TEXT NOT NULL,
    source_url TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    PRIMARY KEY (pair_id, reference_number)
);
CREATE TABLE IF NOT EXISTS ddinter_contextual_alternatives (
    id INTEGER PRIMARY KEY,
    pair_id INTEGER NOT NULL REFERENCES ddinter_interactions(pair_id),
    original_drug_id INTEGER NOT NULL REFERENCES ddinter_drugs(id),
    side TEXT NOT NULL CHECK (side IN ('A', 'B')),
    atc_code TEXT,
    alternative_drug_id INTEGER NOT NULL REFERENCES ddinter_drugs(id),
    source_url TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    UNIQUE (pair_id, side, alternative_drug_id)
);
CREATE TABLE IF NOT EXISTS ddinter_alternatives (
    id INTEGER PRIMARY KEY,
    original_drug_id INTEGER NOT NULL REFERENCES ddinter_drugs(id),
    alternative_drug_id INTEGER REFERENCES ddinter_drugs(id),
    information TEXT,
    context TEXT,
    CHECK (alternative_drug_id IS NOT NULL OR coalesce(length(trim(information)), 0) > 0),
    CHECK (alternative_drug_id IS NULL OR original_drug_id != alternative_drug_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ddinter_alternative_identity
ON ddinter_alternatives (
    original_drug_id, coalesce(alternative_drug_id, 0),
    coalesce(information, ''), coalesce(context, '')
);
"""


def database_path() -> Path:
    default = Path(__file__).resolve().parent.parent / "db" / "ddinter.sqlite"
    return Path(os.getenv("DDINTER_DB_PATH", str(default))).expanduser().resolve()


def connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    connection = sqlite3.connect(
        path.resolve().as_uri() + "?mode=ro" if readonly else str(path),
        uri=readonly,
        check_same_thread=False,
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    """Explicit importer/setup step, never a side effect of serving a request."""
    connection.executescript(SCHEMA)


class Repository:
    """Indexed SQLite access. Caller owns the connection and transaction boundary."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def get_drug(self, drug_id: int) -> Drug | None:
        row = self.connection.execute("SELECT * FROM ddinter_drugs WHERE id = ?", (drug_id,)).fetchone()
        return Drug(**dict(row)) if row else None

    def resolve(self, name: str) -> Drug | None:
        key = normalize_name(name)
        row = self.connection.execute(
            """SELECT * FROM ddinter_drugs WHERE normalized_name = ?
               UNION SELECT d.* FROM ddinter_drugs d JOIN ddinter_aliases a
               ON a.drug_id = d.id WHERE a.normalized_name = ?""", (key, key)
        ).fetchone()
        return Drug(**dict(row)) if row else None

    def by_ddinter_id(self, source_id: str) -> Drug | None:
        row = self.connection.execute(
            "SELECT * FROM ddinter_drugs WHERE ddinter_id = ?", (source_id.strip(),)
        ).fetchone()
        return Drug(**dict(row)) if row else None

    def search(self, query: str, limit: int = 20) -> list[Drug]:
        # instr treats %, _ and quotes as literal user input, not SQL wildcards.
        key = normalize_name(query)
        rows = self.connection.execute(
            """SELECT d.* FROM ddinter_drugs d WHERE instr(d.normalized_name, ?) > 0
               OR EXISTS (SELECT 1 FROM ddinter_aliases a WHERE a.drug_id = d.id
                          AND instr(a.normalized_name, ?) > 0)
               ORDER BY d.normalized_name, d.id LIMIT ?""", (key, key, limit)
        ).fetchall()
        return [Drug(**dict(row)) for row in rows]

    def ensure_drug(self, name: str, ddinter_id: str | None = None,
                    drugbank_id: str | None = None) -> tuple[Drug, bool]:
        key = normalize_name(name)
        if not key:
            raise ValueError("Empty canonical drug name")
        ddinter_id = ddinter_id.strip() or None if ddinter_id is not None else None
        existing = self.resolve(name)
        source_match = self.by_ddinter_id(ddinter_id) if ddinter_id else None
        if source_match and (not existing or source_match.id != existing.id):
            if existing and existing.ddinter_id and existing.id != source_match.id:
                raise ValueError("Canonical name has a different DDInter ID")
            if drugbank_id:
                self.connection.execute(
                    "UPDATE ddinter_drugs SET drugbank_id = coalesce(?, drugbank_id) WHERE id = ?",
                    (drugbank_id, source_match.id),
                )
                source_match = self.get_drug(source_match.id)
            return source_match, False
        if existing:
            if ddinter_id and existing.ddinter_id not in (None, ddinter_id):
                raise ValueError("Canonical name has a different DDInter ID")
            if ddinter_id and not existing.ddinter_id:
                self.connection.execute(
                    "UPDATE ddinter_drugs SET ddinter_id = ?, drugbank_id = coalesce(?, drugbank_id) WHERE id = ?",
                    (ddinter_id, drugbank_id, existing.id),
                )
                existing = self.get_drug(existing.id)
            elif drugbank_id:
                self.connection.execute(
                    "UPDATE ddinter_drugs SET drugbank_id = coalesce(?, drugbank_id) WHERE id = ?",
                    (drugbank_id, existing.id),
                )
                existing = self.get_drug(existing.id)
            return existing, False
        cursor = self.connection.execute(
            "INSERT INTO ddinter_drugs (canonical_name, normalized_name, ddinter_id, drugbank_id) VALUES (?, ?, ?, ?)",
            (" ".join(name.split()), key, ddinter_id, drugbank_id),
        )
        return self.get_drug(cursor.lastrowid), True

    def add_alias(self, alias: str, drug_id: int) -> bool:
        key = normalize_name(alias)
        if not key:
            raise ValueError("Empty alias")
        existing = self.resolve(alias)
        if existing:
            if existing.id != drug_id:
                raise ValueError("Alias already identifies a different drug")
            return False
        self.connection.execute(
            "INSERT INTO ddinter_aliases (alias, normalized_name, drug_id) VALUES (?, ?, ?)",
            (alias.strip(), key, drug_id),
        )
        return True

    def get_interaction(self, interaction_id: int) -> DrugInteraction | None:
        row = self.connection.execute(
            """SELECT i.*, d.management AS detail_management, d.interaction_text AS detail_interaction_text,
                      d.pair_id AS detail_pair_id,
                      CASE WHEN d.pair_id IS NULL THEN 0 ELSE 1 END AS detail_available
               FROM ddinter_interactions i LEFT JOIN ddinter_pair_details d ON d.pair_id = i.pair_id
                    WHERE i.id = ? OR i.pair_id = ? ORDER BY CASE WHEN i.pair_id = ? THEN 0 ELSE 1 END LIMIT 1""",
                (interaction_id, interaction_id, interaction_id),
        ).fetchone()
        if not row:
            return None
        values = dict(row)
        values.pop("detail_pair_id", None)
        values["management"] = values.pop("detail_management") or values.get("management")
        values["interaction_text"] = values.pop("detail_interaction_text") or values.get("interaction_text")
        values["references"] = self._references(values.get("pair_id"))
        return DrugInteraction(**values)

    def find_pair(self, first: int, second: int) -> DrugInteraction | None:
        row = self.connection.execute(
            """SELECT i.*, d.management AS detail_management, d.interaction_text AS detail_interaction_text,
                      CASE WHEN d.pair_id IS NULL THEN 0 ELSE 1 END AS detail_available
               FROM ddinter_interactions i LEFT JOIN ddinter_pair_details d ON d.pair_id = i.pair_id
               WHERE i.drug_a_id = ? AND i.drug_b_id = ? ORDER BY i.pair_id, i.id LIMIT 1""",
            tuple(sorted((first, second))),
        ).fetchone()
        if not row:
            return None
        values = dict(row)
        values["management"] = values.pop("detail_management") or values.get("management")
        values["interaction_text"] = values.pop("detail_interaction_text") or values.get("interaction_text")
        values["references"] = self._references(values.get("pair_id"))
        return DrugInteraction(**values)

    def interactions_for(self, drug_ids: list[int]) -> list[DrugInteraction]:
        if len(drug_ids) < 2:
            return []
        slots = ",".join("?" for _ in drug_ids)
        rows = self.connection.execute(
            f"""SELECT i.*, d.management AS detail_management, d.interaction_text AS detail_interaction_text,
                       CASE WHEN d.pair_id IS NULL THEN 0 ELSE 1 END AS detail_available
                FROM ddinter_interactions i LEFT JOIN ddinter_pair_details d ON d.pair_id = i.pair_id
                WHERE i.drug_a_id IN ({slots}) AND i.drug_b_id IN ({slots})
                ORDER BY i.pair_id, i.id""",
            drug_ids + drug_ids,
        ).fetchall()
        interactions = []
        for row in rows:
            values = dict(row)
            values["management"] = values.pop("detail_management") or values.get("management")
            values["interaction_text"] = values.pop("detail_interaction_text") or values.get("interaction_text")
            values["references"] = self._references(values.get("pair_id"))
            interactions.append(DrugInteraction(**values))
        return interactions

    def _references(self, pair_id: int | None) -> list[dict]:
        if pair_id is None:
            return []
        rows = self.connection.execute(
            "SELECT pair_id, reference_number, reference_text, source_url FROM ddinter_references "
            "WHERE pair_id = ? ORDER BY reference_number", (pair_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def add_interaction(self, first: int, second: int, severity: str = "unknown", **details) -> bool:
        if first == second:
            raise ValueError("Self-interactions are not supported")
        fields = ("interaction_type", "description", "mechanism", "management", "source_reference")
        if set(details) - set(fields):
            raise ValueError("Unsupported interaction field")
        values = {field: details.get(field) or None for field in fields}
        severity = normalize_name(severity) or "unknown"
        existing = self.find_pair(first, second)
        if existing:
            if existing.severity != severity or any(getattr(existing, k) != v for k, v in values.items()):
                raise ValueError("Conflicting records for the same unordered interaction pair")
            return False
        self.connection.execute(
            """INSERT INTO ddinter_interactions
               (drug_a_id, drug_b_id, severity, interaction_type, description, mechanism, management, source_reference)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (*sorted((first, second)), severity, *values.values()),
        )
        return True

    def alternatives(self, drug_id: int, pair_id: int | None = None) -> list[AlternativeDrug]:
        if pair_id is not None:
            rows = self.connection.execute(
                """SELECT id, original_drug_id, alternative_drug_id, NULL AS information,
                          NULL AS context, pair_id, side, atc_code
                   FROM ddinter_contextual_alternatives
                   WHERE original_drug_id = ? AND pair_id = ? ORDER BY id""", (drug_id, pair_id)
            ).fetchall()
            return [AlternativeDrug(**dict(row)) for row in rows]
        rows = self.connection.execute(
            "SELECT * FROM ddinter_alternatives WHERE original_drug_id = ? ORDER BY id", (drug_id,)
        ).fetchall()
        return [AlternativeDrug(**dict(row)) for row in rows]

    def add_definition(self, definition_id: str, *, severity: str, mechanism: str,
                       description: str, source_url: str, scraped_at: str) -> bool:
        exists = self.connection.execute(
            "SELECT 1 FROM ddinter_definitions WHERE definition_id = ?", (str(definition_id),)
        ).fetchone() is not None
        cursor = self.connection.execute(
            """INSERT INTO ddinter_definitions
               (definition_id, severity, mechanism, description, source_url, scraped_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(definition_id) DO UPDATE SET severity=excluded.severity,
               mechanism=excluded.mechanism, description=excluded.description,
               source_url=excluded.source_url, scraped_at=excluded.scraped_at""",
            (str(definition_id), severity, mechanism, description or None, source_url, scraped_at),
        )
        return not exists

    def add_contract_interaction(self, *, pair_id: int, definition_id: str, first: int,
                                 second: int, severity: str, mechanism: str,
                                 pair_key: str, detail_url: str) -> bool:
        if first == second:
            raise ValueError("Self-interactions are not supported")
        severity = {"major": "Major", "moderate": "Moderate", "minor": "Minor", "unknown": "Unknown"}.get(
            normalize_name(severity), "Unknown"
        )
        normalized_definition = str(definition_id).strip() or None
        if normalized_definition == "-1":
            normalized_definition = None
        existing = self.connection.execute(
            "SELECT definition_id, severity, mechanism FROM ddinter_interactions WHERE pair_id = ?",
            (pair_id,),
        ).fetchone()
        if existing:
            existing_severity = existing["severity"]
            existing_mechanism = existing["mechanism"]
            enriched_severity = severity if severity != "Unknown" or existing_severity in (None, "Unknown") else existing_severity
            enriched_mechanism = mechanism if normalize_name(mechanism) not in ("", "unknown") or not existing_mechanism else existing_mechanism
            enriched_definition = normalized_definition or existing["definition_id"]
        else:
            enriched_severity = severity
            enriched_mechanism = mechanism or "Unknown"
            enriched_definition = normalized_definition
        cursor = self.connection.execute(
            """INSERT INTO ddinter_interactions
               (drug_a_id, drug_b_id, severity, mechanism, pair_id, definition_id, pair_key, detail_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(pair_id) DO UPDATE SET drug_a_id=excluded.drug_a_id,
               drug_b_id=excluded.drug_b_id, severity=excluded.severity,
               mechanism=excluded.mechanism, definition_id=excluded.definition_id,
               pair_key=coalesce(excluded.pair_key, ddinter_interactions.pair_key),
               detail_url=coalesce(excluded.detail_url, ddinter_interactions.detail_url)""",
            (*sorted((first, second)), enriched_severity, enriched_mechanism, pair_id,
             enriched_definition, pair_key or None, detail_url or None),
        )
        return existing is None

    def add_pair_detail(self, pair_id: int, *, interaction_text: str, management: str,
                        references_text: str, alternative_a: str, alternative_b: str,
                        source_url: str, scraped_at: str) -> bool:
        exists = self.connection.execute(
            "SELECT 1 FROM ddinter_pair_details WHERE pair_id = ?", (pair_id,)
        ).fetchone() is not None
        self.connection.execute(
            """INSERT INTO ddinter_pair_details
               (pair_id, interaction_text, management, references_text, alternative_a,
                alternative_b, source_url, scraped_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(pair_id) DO UPDATE SET interaction_text=excluded.interaction_text,
               management=excluded.management, references_text=excluded.references_text,
               alternative_a=excluded.alternative_a, alternative_b=excluded.alternative_b,
               source_url=coalesce(excluded.source_url, ddinter_pair_details.source_url),
               scraped_at=coalesce(excluded.scraped_at, ddinter_pair_details.scraped_at)""",
            (pair_id, interaction_text or None, management or None, references_text or None,
             alternative_a or None, alternative_b or None, source_url, scraped_at),
        )
        self.connection.execute(
            "UPDATE ddinter_interactions SET detail_available = 1, interaction_text = ? WHERE pair_id = ?",
            (interaction_text or None, pair_id),
        )
        return not exists

    def add_reference(self, pair_id: int, reference_number: int, *, reference_text: str,
                      source_url: str, scraped_at: str) -> bool:
        exists = self.connection.execute(
            "SELECT 1 FROM ddinter_references WHERE pair_id = ? AND reference_number = ?",
            (pair_id, reference_number),
        ).fetchone() is not None
        self.connection.execute(
            """INSERT INTO ddinter_references
               (pair_id, reference_number, reference_text, source_url, scraped_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(pair_id, reference_number) DO UPDATE SET
               reference_text=excluded.reference_text, source_url=excluded.source_url,
               scraped_at=excluded.scraped_at""",
            (pair_id, reference_number, reference_text, source_url, scraped_at),
        )
        return not exists

    def add_contextual_alternative(self, *, pair_id: int, original_drug_id: int, side: str,
                                   atc_code: str, alternative_drug_id: int, source_url: str,
                                   scraped_at: str) -> bool:
        if original_drug_id == alternative_drug_id:
            raise ValueError("Alternative cannot equal original drug")
        exists = self.connection.execute(
            """SELECT 1 FROM ddinter_contextual_alternatives
               WHERE pair_id = ? AND side = ? AND alternative_drug_id = ?""",
            (pair_id, side, alternative_drug_id),
        ).fetchone() is not None
        self.connection.execute(
            """INSERT INTO ddinter_contextual_alternatives
               (pair_id, original_drug_id, side, atc_code, alternative_drug_id, source_url, scraped_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(pair_id, side, alternative_drug_id) DO UPDATE SET
               atc_code=excluded.atc_code, source_url=excluded.source_url, scraped_at=excluded.scraped_at""",
            (pair_id, original_drug_id, side, atc_code or None, alternative_drug_id, source_url, scraped_at),
        )
        return not exists

    def add_alternative(self, original: int, alternative: int | None = None,
                        information: str | None = None, context: str | None = None) -> bool:
        information = information.strip() or None if information is not None else None
        context = context.strip() or None if context is not None else None
        if alternative == original or (alternative is None and not information):
            raise ValueError("Alternative needs a different drug or nonempty textual information")
        cursor = self.connection.execute(
            """INSERT INTO ddinter_alternatives
               (original_drug_id, alternative_drug_id, information, context) VALUES (?, ?, ?, ?)
               ON CONFLICT DO NOTHING""", (original, alternative, information, context)
        )
        return cursor.rowcount == 1
