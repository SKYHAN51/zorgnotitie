from app.schemas import ExtractionDraft


def determine_alerts(draft: ExtractionDraft) -> list[dict]:
    """Deterministic, rule-based attention flags. No AI scoring, no
    severity levels, no clinical judgment — each rule reads one explicit
    boolean field the caregiver has reviewed and approved. This function
    is pure: given the same draft, it always returns the same alerts."""
    alerts: list[dict] = []

    if draft.deviation_detected:
        alerts.append({
            "alert_type": "care_deviation",
            "reason": draft.deviation_reason or "Afwijking van planning gemeld",
        })
    if draft.mood_changed:
        alerts.append({
            "alert_type": "mood_change",
            "reason": draft.mood_observation,
        })
    if draft.behaviour_changed:
        alerts.append({
            "alert_type": "behaviour_change",
            "reason": draft.behaviour_observation,
        })

    return alerts
