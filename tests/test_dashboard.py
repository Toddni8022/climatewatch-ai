from dashboard import app as dashboard


class FakeResponse:
    def __init__(self, text="", payload=None):
        self.text = text
        self._payload = payload or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_fetch_csv_rows_skips_comments(monkeypatch):
    response = FakeResponse("# source\nYear,Value\n2024,1.2\n2025,1.4\n")
    monkeypatch.setattr(dashboard.requests, "get", lambda *args, **kwargs: response)
    assert dashboard.fetch_csv_rows("https://example.test/data.csv")[-1] == {
        "Year": "2025",
        "Value": "1.4",
    }


def test_csv_without_header_has_clear_error(monkeypatch):
    response = FakeResponse("# only comments\nnot csv\n")
    monkeypatch.setattr(dashboard.requests, "get", lambda *args, **kwargs: response)
    try:
        dashboard.fetch_csv_rows("https://example.test/bad")
    except ValueError as exc:
        assert "No CSV header" in str(exc)
    else:
        raise AssertionError("Expected malformed CSV to fail")


def test_briefing_does_not_claim_wrong_sea_level_baseline():
    briefing = dashboard.build_briefing("425", "2025", "1.1", "2013", "8.2", "4.5")
    assert "CSIRO/EPA adjusted sea-level series" in briefing
    assert "1993 baseline" not in briefing


def test_refresh_publishes_complete_snapshot(monkeypatch):
    monkeypatch.setattr(dashboard, "AGENT_STEP_DELAY_SECONDS", 0)
    monkeypatch.setattr(dashboard, "fetch_co2", lambda: "425.1")
    monkeypatch.setattr(dashboard, "fetch_temperature", lambda: ("2025", "1.2"))
    monkeypatch.setattr(dashboard, "fetch_sea_level", lambda: ("2013", "8.1"))
    monkeypatch.setattr(dashboard, "fetch_solar", lambda: "4.6")

    assert dashboard.refresh_data() is True
    data = dashboard.snapshot()
    assert data["status"] == "ready"
    assert data["co2"] == "425.1"
    assert data["error"] == ""
