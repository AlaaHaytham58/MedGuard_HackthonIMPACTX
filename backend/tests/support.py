from ddinter.repository import Repository


def populate_mock_catalog(repository: Repository):
    """TEST DATA ONLY: invented names, aliases and statements; no clinical content."""
    drugs = [repository.ensure_drug(f"Drug {letter}", f"MOCK-{letter}")[0] for letter in "ABCD"]
    a, b, c, d = drugs
    repository.add_alias("Mock Brand A", a.id)
    repository.add_interaction(a.id, b.id, "minor", description="Synthetic test interaction A-B")
    repository.add_interaction(a.id, c.id, "major", description="Synthetic test interaction A-C")
    repository.add_interaction(b.id, c.id, "moderate", description="Synthetic test interaction B-C")
    repository.add_alternative(a.id, d.id, "Synthetic test alternative", "Mock context only")
    repository.connection.commit()
    return drugs
