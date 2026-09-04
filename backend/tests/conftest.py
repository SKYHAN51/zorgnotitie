import pytest
import os


# Set up minimal environment variables for tests
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("OPENAI_API_KEY", "sk-fake-test-key")
os.environ.setdefault("DEMO_API_SECRET", "test-demo-secret")

# Shared by every test module that builds a TestClient — matches the
# DEMO_API_SECRET env var above, so requests through it pass the shared-
# secret dependency by default. Import this instead of hardcoding the
# string a second time.
TEST_AUTH_HEADERS = {"X-Demo-Secret": "test-demo-secret"}


class FakeTable:
    """Minimal stand-in matching real supabase-py chaining:
    .insert(row).execute() appends a new row;
    .update(fields).eq(field, value).execute() mutates matching rows in
    place — this distinction matters because production code must use
    .update() to modify an existing zorgmoment, never .insert() with an
    existing id.

    Regression note (finding C1, 2026-09-04 whole-branch review): this
    fake used to let a bare `client.table(name).execute()` succeed for a
    plain read. Real supabase-py's `client.table(name)` returns a
    `SyncRequestBuilder`, which has NO `.execute()` method at all —
    only `.select()` / `.insert()` / `.update()` / `.upsert()` /
    `.delete()` return an object that has `.execute()`. Because the fake
    was more permissive than the real client, every production read that
    forgot `.select()` (see zorgmomenten.py, dashboard.py) still passed
    against the fake and would have 500'd against a real Supabase
    project. The fake now requires `.select()` (or `.insert()` /
    `.update()`) to have been called before `.execute()` works, raising
    AttributeError otherwise, so this exact bug class fails a test
    immediately instead of only failing in production."""
    def __init__(self, store: dict, name: str):
        self._name = name
        self._store = store.setdefault(name, [])
        self._pending_update: dict | None = None
        self._filter: tuple | None = None
        self._executable = False  # set True by select()/insert()/update()/upsert()/delete()

    def select(self, *_columns, **_kwargs):
        self._executable = True
        return self

    def insert(self, row: dict):
        self._store.append(row)
        self._executable = True
        return self

    def update(self, fields: dict):
        self._pending_update = fields
        self._executable = True
        return self

    def eq(self, field: str, value):
        self._filter = (field, value)
        return self

    def execute(self):
        if not self._executable:
            # Mirrors real supabase-py: SyncRequestBuilder (what
            # client.table(...) returns) has no .execute() at all.
            raise AttributeError(
                f"'FakeTable' object for table '{self._name}' has no attribute "
                "'execute' — call .select(), .insert(), .update(), .upsert(), "
                "or .delete() first, same as the real supabase-py client."
            )
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


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The rate limiter's in-memory counters live on the single app
    instance every test file imports — without a reset, request counts
    accumulate across the whole test session and a strict per-route limit
    (e.g. /record's 10/minute) could trip from unrelated tests' traffic,
    not the test actually exercising it."""
    from app.main import app
    app.state.limiter._storage.reset()
    yield
