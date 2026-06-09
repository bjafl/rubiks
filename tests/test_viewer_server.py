import json
import threading
import time
import urllib.request
import urllib.error
import pytest


@pytest.fixture(scope="module")
def running_server():
    from mcp_server import viewer_server as vs
    t = threading.Thread(target=vs.run, daemon=True)
    t.start()
    time.sleep(0.6)
    yield vs


def test_http_serves_index(running_server):
    resp = urllib.request.urlopen("http://localhost:8766/")
    assert resp.status == 200
    html = resp.read().decode()
    assert "<html" in html.lower()


def test_http_serves_geometry(running_server):
    resp = urllib.request.urlopen("http://localhost:8766/geometry.json")
    assert resp.status == 200
    data = json.loads(resp.read())
    assert "faceNames" in data


def _post_cmd(cmd: dict) -> dict:
    body = json.dumps(cmd).encode()
    req = urllib.request.Request(
        "http://localhost:8766/api/command",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def test_api_reset(running_server):
    result = _post_cmd({"type": "reset"})
    assert result["ok"] is True


def test_api_load_algorithm(running_server):
    from mcp_server.viewer_server import VIEWER_STATE
    _post_cmd({"type": "load_algorithm", "name": "CO9"})
    assert VIEWER_STATE.alg_name == "CO9"
    assert len(VIEWER_STATE.sequence) == 11


def test_api_step_forward(running_server):
    from mcp_server.viewer_server import VIEWER_STATE
    _post_cmd({"type": "load_algorithm", "name": "CO9"})
    before = VIEWER_STATE.move_index
    _post_cmd({"type": "step_forward"})
    assert VIEWER_STATE.move_index == before + 1


def test_api_unknown_command_returns_400(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _post_cmd({"type": "bogus_command"})
    assert exc_info.value.code == 400
