# backend/tests/test_faketable_matches_postgrest.py
"""Regression test for finding C1 (whole-branch review, 2026-09-04).

Every production DB read used to call `client.table(name).execute()`
directly, skipping `.select()`. That passed against the old, overly
permissive FakeTable but would 500 against a real Supabase project,
because `client.table(name)` returns postgrest's `SyncRequestBuilder`,
which has no `.execute()` method at all.

This test asserts the fake's method surface can't drift from the real
one again: any bare `client.table(...).execute()` call — the exact
mistake that caused C1 — must raise, in both the fake and the real
postgrest client.
"""
import pytest
from postgrest import SyncRequestBuilder, SyncQueryRequestBuilder


def test_real_sync_request_builder_has_no_bare_execute():
    """Documents the real-library contract this whole fix wave is built
    on: client.table(name) returns SyncRequestBuilder, which has no
    .execute(); only .select()/.insert()/.update()/.upsert()/.delete()
    return something with .execute() (SyncQueryRequestBuilder or a
    subclass of it)."""
    assert "execute" not in dir(SyncRequestBuilder)
    assert "execute" in dir(SyncQueryRequestBuilder)


def test_faketable_rejects_bare_execute_without_select(fake_supabase):
    """Mirrors the real client: a bare client.table(name).execute() with
    no .select()/.insert()/.update() first must raise, not silently
    return data. If this test ever fails to raise, the fake has drifted
    permissive again and C1-style bugs can hide behind the test suite."""
    with pytest.raises(AttributeError):
        fake_supabase.table("zorgmomenten").execute()


def test_faketable_allows_execute_after_select(fake_supabase):
    fake_supabase.table("zorgmomenten").insert({"id": "zm-1"}).execute()
    rows = fake_supabase.table("zorgmomenten").select("*").execute().data
    assert rows == [{"id": "zm-1"}]
