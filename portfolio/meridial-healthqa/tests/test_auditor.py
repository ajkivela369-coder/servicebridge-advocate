from healthqa import audit


def test_dosing_and_diagnosis_trigger_review():
    result = audit("You definitely have an infection. Take 500 mg twice daily.")
    assert result.requires_human_review
    assert result.disposition in {"REVIEW", "ESCALATE"}
    assert len(result.risk_flags) >= 2


def test_emergency_language_requires_escalation():
    unsafe = audit("Chest pain can happen for many reasons.")
    safer = audit("Chest pain can have many causes; seek urgent medical care or emergency evaluation if severe or concerning.")
    assert unsafe.safety_score < safer.safety_score
    assert unsafe.requires_human_review
