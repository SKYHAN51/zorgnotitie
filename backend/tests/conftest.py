import pytest


class FakeTable:
    """Minimal stand-in matching real supabase-py chaining:
    .insert(row).execute() appends a new row;
    .update(fields).eq(field, value).execute() mutates matching rows in
    place — this distinction matters because production code must use
    .update() to modify an existing zorgmoment, never .insert() with an
    existing id."""
    def __init__(self, store: dict, name: str):
        self._store = store.setdefault(name, [])
        self._pending_update: dict | None = None
        self._filter: tuple | None = None

    def insert(self, row: dict):
        self._store.append(row)
        return self

    def update(self, fields: dict):
        self._pending_update = fields
        return self

    def eq(self, field: str, value):
        self._filter = (field, value)
        return self

    def execute(self):
        if self._pending_update is not None and self._filter is not None:
            field, value = self._filter
            matched = [r for r in self._store if r.get(field) == value]
            for row in matched:
                row.update(self._pending_update)
            self._pending_update, self._filter = None, None
            return type("Result", (), {"data": matched})()
        return type("Result", (), {"data": list(self._store)})()


class FakeSupabaseClient:
    """Minimal stand-in for supabase.Client — records inserted rows
    per table in memory so tests can assert on them without a real
    Supabase project."""
    def __init__(self):
        self._data: dict = {}

    def table(self, name: str):
        return FakeTable(self._data, name)


@pytest.fixture
def fake_supabase():
    return FakeSupabaseClient()
