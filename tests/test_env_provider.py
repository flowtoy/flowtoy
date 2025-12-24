from flowtoy.providers.env import EnvProvider


def test_env_provider(monkeypatch):
    monkeypatch.setenv("TEST_A", "value-a")
    monkeypatch.setenv("TEST_B", "value-b")
    cfg = {"vars": ["TEST_A", "TEST_B", "MISSING"]}
    ec = EnvProvider(cfg)
    res = ec.call()
    assert res["status"]["success"] is True
    assert res["data"]["TEST_A"] == "value-a"
    assert res["data"]["TEST_B"] == "value-b"
    assert res["data"]["MISSING"] is None
