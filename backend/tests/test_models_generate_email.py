from backend.models.generate_email import GenerateEmailResult


def test_generate_email_result_roundtrip():
    result = GenerateEmailResult(html="<html></html>")
    assert result.html == "<html></html>"
