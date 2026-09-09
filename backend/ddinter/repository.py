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
    ddinter_id TEXT UNIQUE
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
    CHECK (drug_a_id < drug_b_id),
    UNIQUE (drug_a_id, drug_b_id)
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

    def ensure_drug(self, name: str, ddinter_id: str | None = None) -> tuple[Drug, bool]:
        key = normalize_name(name)
        if not key:
            raise ValueError("Empty canonical drug name")
        ddinter_id = ddinter_id.strip() or None if ddinter_id is not None else None
        existing = self.resolve(name)
        source_match = self.by_ddinter_id(ddinter_id) if ddinter_id else None
        if source_match and (not existing or source_match.id != existing.id):
            raise ValueError("DDInter ID conflicts with a canonical name; supply an explicit alias")
        if existing:
            if ddinter_id and existing.ddinter_id not in (None, ddinter_id):
                raise ValueError("Canonical name has a different DDInter ID")
            if ddinter_id and not existing.ddinter_id:
                self.connection.execute(
                    "UPDATE ddinter_drugs SET ddinter_id = ? WHERE id = ?", (ddinter_id, existing.id)
                )
                existing = self.get_drug(existing.id)
            return existing, False
        cursor = self.connection.execute(
            "INSERT INTO ddinter_drugs (canonical_name, normalized_name, ddinter_id) VALUES (?, ?, ?)",
            (" ".join(name.split()), key, ddinter_id),
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
            "SELECT * FROM ddinter_interactions WHERE id = ?", (interaction_id,)
        ).fetchone()
        return DrugInteraction(**dict(row)) if row else None

    def find_pair(self, first: int, second: int) -> DrugInteraction | None:
        row = self.connection.execute(
            "SELECT * FROM ddinter_interactions WHERE drug_a_id = ? AND drug_b_id = ?",
            tuple(sorted((first, second))),
        ).fetchone()
        return DrugInteraction(**dict(row)) if row else None

    def interactions_for(self, drug_ids: list[int]) -> list[DrugInteraction]:
        if len(drug_ids) < 2:
            return []
        slots = ",".join("?" for _ in drug_ids)
        rows = self.connection.execute(
            f"SELECT * FROM ddinter_interactions WHERE drug_a_id IN ({slots}) AND drug_b_id IN ({slots})",
            drug_ids + drug_ids,
        ).fetchall()
        return [DrugInteraction(**dict(row)) for row in rows]

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

    def alternatives(self, drug_id: int) -> list[AlternativeDrug]:
        rows = self.connection.execute(
            "SELECT * FROM ddinter_alternatives WHERE original_drug_id = ? ORDER BY id", (drug_id,)
        ).fetchall()
        return [AlternativeDrug(**dict(row)) for row in rows]

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
