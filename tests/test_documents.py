import pytest
from contract_risk.documents import extract_text

def test_txt():
    assert "contract" in extract_text("sample.txt", b"contract text")

def test_bad_extension():
    with pytest.raises(ValueError):
        extract_text("sample.exe", b"x")
