import pytest

flask = pytest.importorskip("flask")
pytest.importorskip("matplotlib")

from bfid.web import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_index_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"bfid" in r.data


def test_api_demo(client):
    r = client.post("/api/demo", json={
        "persons": 3, "traces": 4, "frames": 60, "window": 16, "stride": 8})
    assert r.status_code == 200
    d = r.get_json()
    assert d["n_classes"] == 3
    assert 0.0 <= d["accuracy"] <= 1.0
    assert d["confusion_png"].startswith("data:image/png;base64,")
    assert d["folds_png"].startswith("data:image/png;base64,")


def test_api_demo_zones_mode(client):
    r = client.post("/api/demo", json={"persons": 3, "traces": 3, "frames": 50,
                                       "mode": "zones"})
    assert r.status_code == 200
    assert r.get_json()["mode"] == "zone"


def test_api_signature(client):
    r = client.post("/api/signature", json={"persons": 4, "index": 1, "frames": 60})
    assert r.status_code == 200
    d = r.get_json()
    assert d["label"] == "person_1"
    assert d["signature_png"].startswith("data:image/png;base64,")


def test_api_pcap_no_file(client):
    r = client.post("/api/pcap", data={})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_param_clamping(client):
    # persons=9999 doit être borné, pas planter le serveur.
    r = client.post("/api/demo", json={"persons": 9999, "traces": 2, "frames": 40})
    assert r.status_code == 200
    assert r.get_json()["n_classes"] <= 12
