from app.schemas import ExtractionDraft
from app.alerts import determine_alerts


def _draft(**overrides):
    base = dict(
        actual_care_summary="Alles volgens plan.",
        deviation_detected=False,
        deviation_reason=None,
        mood_observation="geen verandering",
        mood_changed=False,
        behaviour_observation="geen bijzonderheden",
        behaviour_changed=False,
    )
    base.update(overrides)
    return ExtractionDraft(**base)


def test_no_triggers_produces_no_alerts():
    alerts = determine_alerts(_draft())
    assert alerts == []


def test_deviation_produces_care_deviation_alert():
    draft = _draft(deviation_detected=True, deviation_reason="Cliënt weigerde douchen")
    alerts = determine_alerts(draft)
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "care_deviation"
    assert alerts[0]["reason"] == "Cliënt weigerde douchen"


def test_mood_changed_produces_mood_change_alert():
    draft = _draft(mood_changed=True, mood_observation="stiller dan normaal")
    alerts = determine_alerts(draft)
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "mood_change"
    assert alerts[0]["reason"] == "stiller dan normaal"


def test_behaviour_changed_produces_behaviour_change_alert():
    draft = _draft(behaviour_changed=True, behaviour_observation="verminderde eetlust")
    alerts = determine_alerts(draft)
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "behaviour_change"
    assert alerts[0]["reason"] == "verminderde eetlust"


def test_all_three_triggers_produce_three_alerts():
    draft = _draft(
        deviation_detected=True, deviation_reason="reden",
        mood_changed=True, mood_observation="stemming",
        behaviour_changed=True, behaviour_observation="gedrag",
    )
    alerts = determine_alerts(draft)
    types = {a["alert_type"] for a in alerts}
    assert types == {"care_deviation", "mood_change", "behaviour_change"}


def test_alert_reason_never_contains_risk_language():
    """Copy guarantee from the spec: never phrase an alert as a clinical
    risk finding. This test guards the reason text pass-through — the
    caller (save endpoint) is responsible for the alert_type -> display
    label mapping, but the raw reason must never be rewritten to add
    risk/diagnosis language."""
    draft = _draft(deviation_detected=True, deviation_reason="Cliënt voelde zich moe")
    alerts = determine_alerts(draft)
    for a in alerts:
        assert "risico" not in a["reason"].lower()
        assert "diagnose" not in a["reason"].lower()
