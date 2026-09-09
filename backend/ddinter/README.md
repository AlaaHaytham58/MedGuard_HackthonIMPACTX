# Local interaction catalog foundation

This is a backend-only DDInter catalog foundation. The current scraper contract is
implemented at the importer boundary; the final scrape is still incomplete.
It makes no network requests and contains no production seed data or medical name
mappings. All fixtures in `backend/tests/support.py` are synthetic test data.

## Existing branch and integration

The inspected branch was `farah-backend`, with a clean working tree. It has FastAPI,
plain `APIRouter` modules, a plain-function vision service, dotenv/environment
configuration, and unpinned pip requirements. Existing endpoints are `/extract`
and `/health`, with no API prefix/version. There was no database implementation,
ORM, migration workflow, automated test suite, lint/type configuration or build
configuration. The root project guides propose SQLite; they describe additional
normalization and pipeline functionality that is not implemented on this branch.

The new `ddinter` package uses standard-library `sqlite3`, existing FastAPI/Pydantic,
and synchronous routes consistent with the existing app. It owns its persistence,
schemas, service, importer and router. `main.py` only gains a router import and
registration. It does not change `/extract`, implement `/normalize` or `/pipeline`,
or add the future guide's `/check` contract. A future pipeline can call
`InteractionService(repository).check_names(names)` in process, or call
`check_pair(first_drug, second_drug)` with canonical `Drug` objects.

## Storage and entities

The authoritative source identity is the DDInter drug ID from `interaction_pairs.csv`.
Display-name normalization is used only for lookup and presentation. DrugBank IDs are
preserved when supplied. `pair_id` is the authoritative concrete interaction identity;
`pair_key` is only an unordered lookup representation, so distinct pair IDs are retained
even when their drug IDs collide. `pair_details` is optional enrichment and its absence
does not remove the interaction.

Tables are namespaced to keep integration with a newer backend straightforward:

| Table | Stored information and constraints |
| --- | --- |
| `ddinter_drugs` | Internal integer ID, canonical display name, unique normalized name, optional unique DDInter ID |
| `ddinter_aliases` | Alias, unique normalized alias, canonical drug foreign key |
| `ddinter_interactions` | Canonical drug IDs, DDInter `pair_id`, definition ID, severity, mechanism, detail URL and optional enrichment; unordered pair uniqueness is not imposed |
| `ddinter_definitions` | Reusable DDInter interaction definitions keyed by `definition_id` |
| `ddinter_pair_details` | Optional pair-specific interaction text and management enrichment |
| `ddinter_references` | Normalized ordered references keyed by pair and reference number |
| `ddinter_contextual_alternatives` | Pair-scoped alternative, original side, ATC code and source provenance |
| `ddinter_alternatives` | Legacy synthetic compatibility table; real DDInter alternatives use the contextual table above |

Foreign keys are enabled on every connection. Pair IDs are sorted before insertion;
database checks require `drug_a_id < drug_b_id`, preventing reversed and self-pairs
even in direct SQL. Alternative identity includes original, target, text and context,
with NULLs handled by a unique expression index. Repository writes reject aliases
that would identify another drug. All catalog writes should use the repository or
importer to preserve name/alias consistency across the two tables.

There are no migrations because the existing branch has no migration workflow.
The importer explicitly initializes its own tables using `CREATE IF NOT EXISTS`;
it does not migrate incompatible preexisting table definitions. Schema initialization
is separate from the import transaction, so a failed first import can leave empty
tables, but never partially committed rows. Future structural changes require an
explicit migration or rebuilding a separate catalog from source files.

`DDINTER_DB_PATH` selects the database. Its default is `backend/db/ddinter.sqlite`,
independent of the server working directory. Relative environment paths are resolved
against the process working directory. Use an absolute path in deployments. The
server opens the catalog read-only per request and closes each connection. It never
creates or seeds a database while serving requests. Missing/uninitialized catalogs
return HTTP 503 `CATALOG_UNAVAILABLE`; an initialized empty catalog returns unresolved
drug inputs. The importer must run before the catalog is used.

## Name resolution and interaction behavior

Normalization is a pure function: Unicode NFKC, case folding, trimming and whitespace
collapse. It preserves punctuation, salt names, dose text and combination ingredients.
There is no fuzzy match, dose removal, salt removal, translation or inferred brand
mapping. Search is a bounded literal substring search over canonical names and
aliases; checking requires exact normalized canonical/alias resolution.

Multi-drug checking accepts 2–50 inputs, each 1–300 characters and not whitespace-only.
It preserves a resolution result for every input, deduplicates resolved canonical IDs,
generates each unordered pair once, and retrieves matching interactions in one query.
Three distinct resolved drugs yield three comparisons. Repeated names and aliases
for the same canonical drug add no self-pairs or duplicate comparisons.

The check response contains:

- `status`: `complete`, `unresolved_drugs`, or `insufficient_distinct_drugs`.
- `resolutions`: original input, normalized input, resolution status and canonical drug.
- `comparisons`: number of unique pairs of resolved drugs actually checked.
- `interactions`: found records with both canonical drugs and `interaction_found` status.
- `no_record_pairs`: checked pairs with `no_record_found` status and no interaction.
- `notice`: absence of a record does not establish medical safety.

Known pairs are still checked when other inputs are unresolved. `complete` means all
inputs resolved and comparisons finished; it is not a clinical judgment. Duplicates
alone produce `insufficient_distinct_drugs`. Source severity labels are normalized
for presentation and kept visible. Recognized labels rank `Major > Moderate > Minor > Unknown`;
non-contract labels have `severity_rank: null` and appear after ranked records. `Unknown`
is an exported source value and is not inferred to be mild.

Real DDInter alternatives are returned with concrete pair context (`pair_id`, original
side and ATC code). They are not personalized substitution advice.

## API

| Method | Route | Input/result |
| --- | --- | --- |
| GET | `/drugs/search?q=...&limit=20` | Canonical drugs matching a name or alias; maximum limit 100 |
| GET | `/interactions/check?drug_a=...&drug_b=...` | Same explicit check response as multi-drug checking |
| POST | `/interactions/check-multiple` | JSON `{"drugs": ["Drug A", "Drug B", "Drug C"]}`; names here are illustrative synthetic names |
| GET | `/interactions/{interaction_id}` | Stored interaction details; 404 if absent |
| GET | `/drugs/{drug_id}/alternatives` | Canonical original drug plus stored alternatives; 404 for an unknown drug, empty list for no alternatives |

Pydantic request and response schemas appear in `/docs`. Malformed input uses FastAPI
422 validation. Explicit errors follow the existing `/extract` convention:
`{"detail": {"error": true, "code": "...", "message": "...", "details": {}}}`.
Extra multi-check request fields and non-string drug names are rejected.

## CSV mapping boundary

`importer.FIELDS`, `CONTRACT_FILES`, `contract_sources`, `CsvSource`, and `_import_row`
are the isolated adapter boundary. The current contract maps these files:
`interaction_definitions.csv`, `interaction_pairs.csv`, `pair_details.csv`,
`alternatives.csv`, `references.csv`, and `failures.csv`. No aliases or standalone drug
CSV is required. `failures.csv` is reported as import metadata rather than medical data.
The importer creates/reuses drugs from pair and alternative rows by DDInter ID.

The legacy generic manifest support remains available for synthetic fixtures. The
database and service do not reference CSV headers or filenames. A JSON manifest maps
domain fields to actual CSV headers:

```json
{
  "sources": [
    {
      "kind": "drugs",
      "path": "<actual drug CSV path>",
      "columns": {"canonical_name": "<name header>", "ddinter_id": "<ID header>"}
    },
    {
      "kind": "aliases",
      "path": "<actual alias CSV path>",
      "reference": "ddinter_id",
      "columns": {"drug": "<canonical ID header>", "alias": "<alias header>"}
    },
    {
      "kind": "interactions",
      "path": "<actual interaction CSV path>",
      "reference": "ddinter_id",
      "columns": {
        "drug_a": "<first ID header>", "drug_b": "<second ID header>",
        "severity": "<severity header>", "interaction_type": "<type header>",
        "description": "<details header>", "mechanism": "<mechanism header>",
        "management": "<recommendation header>", "source_reference": "<reference header>"
      }
    },
    {
      "kind": "alternatives",
      "path": "<actual alternatives CSV path>",
      "reference": "ddinter_id",
      "columns": {
        "original_drug": "<original ID header>", "alternative_drug": "<target ID header>",
        "information": "<text header>", "context": "<context header>"
      }
    }
  ]
}
```

Omit absent optional fields and entity sources. Mapped headers must actually exist.
Paths are absolute or relative to the manifest location. `encoding` defaults to
`utf-8-sig` (handles BOM), and `delimiter` to comma; both are configurable per source.
For references, `name` (default) resolves aliases or creates/reuses canonical drugs;
`ddinter_id` requires previously imported canonical IDs. IDs are opaque and case-sensitive.
Drugs import first, then aliases, interactions and alternatives, irrespective of manifest
order. Alias-to-alias chains and mixed ID/name references within one source are not supported.

The adapter currently expects one drug, alias, unordered pair or alternative per row.
Nested JSON, list-valued aliases, multiple alternatives in a cell, HTML cleaning and
multiple directional records per pair require an explicit adapter decision once the
real schema arrives. Exact duplicate pairs are skipped while existing rows are
updated by authoritative `pair_id`. A later non-`Unknown` severity, non-`Unknown`
mechanism or real `definition_id` enriches an earlier partial row; a partial refresh
does not erase known values. Detail, reference and contextual-alternative rows also
upsert by their pair-scoped identities. DDInter IDs are authoritative when a later
row presents a display-name variation; no alias or brand mapping is invented.
Reimport is idempotent for identical input and supports later enrichment without
duplicate rows.

CSV files stream row by row with indexed identity lookups and a single transaction,
avoiding a commit per row. Per-row savepoints prevent partial writes on invalid rows.
Individual inserts allow precise conflict detection and diagnostics without extra
bulk dependencies; actual dataset throughput should be measured when files arrive.
Strict mode rolls back the entire batch on a malformed row. `--skip-malformed` is an
explicit opt-in to commit valid rows and skip invalid ones. Missing/duplicate headers,
unreadable files and invalid CSV syntax abort the batch even in skip mode.

Reports include rows read, drugs/interactions created, aliases/alternatives imported,
duplicates skipped, malformed rows, committed status and up to 20 errors with file
and CSV line. Duplicate counts count unchanged entity rows; attaching a newly supplied
DDInter ID to an existing name also counts as a reused drug row. Strict rollback resets
creation/import/duplicate counts to zero. Schema/file failures return a fatal error.

From `backend`, after preparing the real manifest:

```powershell
.venv/Scripts/python.exe -m ddinter.importer --manifest C:/data/mapping.json --database C:/data/ddinter-review.sqlite
```

No dataset is loaded during app startup. Do not run imports against the live catalog
for initial review: use a separate database, inspect the report and sample records,
then configure `DDINTER_DB_PATH` to the reviewed catalog.

## Verification and handoff

From `backend`:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m compileall -q ddinter tests main.py
```

Tests use `unittest`, temporary databases, synthetic fixtures and FastAPI's TestClient.
`httpx` is the only explicitly added development dependency; runtime requirements are
unchanged. Coverage includes normalization, aliases, unique pairs, duplicates, severity,
missing/unresolved records, database constraints, all five routes, malformed API input,
transaction rollback, import reruns, configurable mapping, conflicts and existing health/
mock-extraction behavior. Tests never call Gemini or DDInter. The installed Starlette
currently emits a deprecation warning for its httpx TestClient adapter; tests still pass.

When the scraper delivers:

1. Inspect actual headers, encoding, delimiters, ID relationships, severity vocabulary,
   null representation, pair directionality, aliases and alternative context. Confirm
   which files are complete exports and which are partial.
2. Create the manifest using actual paths/headers, omit absent optional mappings, and
   adapt only the importer boundary for nested or list-valued cells. Reconcile severity
   ranking with source labels without inferring absent medical information.
3. Add small schema-representative regression fixtures and tests; keep all synthetic
   test content out of the real catalog.
4. Run a strict import into a separate database, investigate malformed/conflicting rows,
   and rerun the identical import to confirm no new duplicate entities appear.
5. Compare source and imported counts; inspect representative records, reversed pairs,
   aliases, missing IDs, unknown severities and alternatives. Check runtime with the
   actual dataset and run the full tests.
6. Configure `DDINTER_DB_PATH` to the reviewed database, smoke-test the five routes,
   and connect the team's normalization/pipeline output to the service in process.

Likely merge conflicts are the two added lines in `main.py` and appended settings in
`.env.example`/`.gitignore`. Everything else is newly added: `ddinter/`, `tests/`, and
`requirements-dev.txt`. If the newer branch introduces a database/ORM, port the narrow
repository boundary to it while retaining normalization, service semantics and tests;
avoid copying this SQLite schema over newer existing drug entities without reconciliation.
