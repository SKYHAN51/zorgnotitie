from app.events import log_event


def test_log_event_inserts_a_row(fake_supabase):
    log_event(
        fake_supabase,
        zorgmoment_id="abc-123",
        stage="stt",
        status="succeeded",
    )
    rows = fake_supabase.table("processing_events").execute().data
    assert len(rows) == 1
    assert rows[0]["zorgmoment_id"] == "abc-123"
    assert rows[0]["stage"] == "stt"
    assert rows[0]["status"] == "succeeded"
    assert rows[0]["error_code"] is None


def test_log_event_records_error_fields(fake_supabase):
    log_event(
        fake_supabase,
        zorgmoment_id="abc-123",
        stage="extraction",
        status="failed",
        error_code="invalid_json",
        error_message_safe="Extraction output did not match the required schema.",
    )
    rows = fake_supabase.table("processing_events").execute().data
    assert rows[0]["status"] == "failed"
    assert rows[0]["error_code"] == "invalid_json"
