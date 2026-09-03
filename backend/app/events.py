from typing import Optional


def log_event(
    client,
    zorgmoment_id: str,
    stage: str,
    status: str,
    error_code: Optional[str] = None,
    error_message_safe: Optional[str] = None,
) -> None:
    """Write one traceability row for a pipeline stage. Called at the
    start and end of every stage (stt, extraction, save) so failures are
    diagnosable from the database, never only from logs."""
    client.table("processing_events").insert({
        "zorgmoment_id": zorgmoment_id,
        "stage": stage,
        "status": status,
        "error_code": error_code,
        "error_message_safe": error_message_safe,
    }).execute()
