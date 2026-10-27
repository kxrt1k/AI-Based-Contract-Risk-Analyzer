from contract_risk import analyze_text

def test_schema_and_findings():
    result = analyze_text("The supplier may terminate this agreement at any time without notice. The customer shall indemnify the supplier.")
    data = result.model_dump()
    assert 0 <= data["overall_risk_score"] <= 100
    assert data["risk_level"] in {"low", "medium", "high", "critical"}
    assert data["statistics"]["word_count"] > 0
    assert data["findings"]
    assert data["disclaimer"]

def test_blank_rejected():
    try:
        analyze_text(" ")
    except ValueError:
        return
    assert False, "Expected ValueError"
