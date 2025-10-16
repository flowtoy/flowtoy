from evans.connectors.rest import RestConnector


class DummyResponse:
    def __init__(self, status_code=200, headers=None, json_data=None, text_data=""):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data
        self.text = text_data

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


def test_rest_connector_json(monkeypatch):
    def fake_request(method, url, params=None, json=None, headers=None):
        return DummyResponse(
            status_code=200, headers={"h": "v"}, json_data={"user": "alice"}
        )

    monkeypatch.setattr("evans.connectors.rest.requests.request", fake_request)
    rc = RestConnector({"url": "https://example.test/api", "method": "GET"})
    res = rc.call(None)
    assert isinstance(res, dict)
    assert res["status"]["success"] is True
    assert res["data"]["user"] == "alice"
    assert res["meta"]["headers"]["h"] == "v"


def test_rest_connector_text(monkeypatch):
    def fake_request(method, url, params=None, json=None, headers=None):
        return DummyResponse(
            status_code=200, headers={}, json_data=None, text_data="plain text"
        )

    monkeypatch.setattr("evans.connectors.rest.requests.request", fake_request)
    rc = RestConnector({"url": "https://example.test/api", "method": "GET"})
    res = rc.call(None)
    assert isinstance(res, dict)
    assert res["status"]["success"] is True
    assert res["data"] == "plain text"


def test_rest_connector_500(monkeypatch):
    def fake_request(method, url, params=None, json=None, headers=None):
        return DummyResponse(
            status_code=500, headers={}, json_data=None, text_data="server error"
        )

    monkeypatch.setattr("evans.connectors.rest.requests.request", fake_request)
    rc = RestConnector({"url": "https://example.test/api", "method": "GET"})
    res = rc.call(None)
    assert isinstance(res, dict)
    assert res["status"]["success"] is False
    assert res["status"]["code"] == 500
    assert "HTTP status 500" in res["status"]["notes"]


def test_rest_connector_404(monkeypatch):
    def fake_request(method, url, params=None, json=None, headers=None):
        return DummyResponse(
            status_code=404, headers={}, json_data=None, text_data="not found"
        )

    monkeypatch.setattr("evans.connectors.rest.requests.request", fake_request)
    rc = RestConnector({"url": "https://example.test/api", "method": "GET"})
    res = rc.call(None)
    assert isinstance(res, dict)
    assert res["status"]["success"] is False
    assert res["status"]["code"] == 404
    assert "HTTP status 404" in res["status"]["notes"]
