"""HTTP static file server + WebSocket server + REST API for the Megaminx viewer.

Run standalone:  python -m mcp_server.viewer_server
HTTP port: 8766  (static files + /api/command)
WS port:   8765
"""
from __future__ import annotations
import asyncio
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import websockets

from megaminx.algorithms import SINGLE_ALGS, get_library
from mcp_server.viewer_state import ViewerState, parse_sequence

VIEWER_DIR = Path(__file__).parent.parent / "viewer"
HTTP_PORT  = 8766
WS_PORT    = 8765

VIEWER_STATE: ViewerState = ViewerState()
_WS_LOOP: asyncio.AbstractEventLoop | None = None


# ── WebSocket ─────────────────────────────────────────────────────────────────

async def _ws_handler(websocket) -> None:
    VIEWER_STATE.ws_clients.add(websocket)
    await websocket.send(json.dumps(VIEWER_STATE.state_snapshot()))
    try:
        async for raw in websocket:
            msg = json.loads(raw)
            if msg.get("type") == "step":
                if msg["dir"] == "fwd":
                    VIEWER_STATE.step_forward()
                else:
                    VIEWER_STATE.step_backward()
                await VIEWER_STATE.broadcast(VIEWER_STATE.state_snapshot())
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        VIEWER_STATE.ws_clients.discard(websocket)


async def _run_ws() -> None:
    global _WS_LOOP
    _WS_LOOP = asyncio.get_running_loop()
    async with websockets.serve(_ws_handler, "localhost", WS_PORT):
        await asyncio.Future()


# ── Command dispatch ──────────────────────────────────────────────────────────

def _handle_command(cmd: dict) -> dict:
    t = cmd.get("type")
    if t == "load_algorithm":
        name = cmd["name"]
        if name not in SINGLE_ALGS:
            raise KeyError(f"Unknown algorithm: {name!r}")
        VIEWER_STATE.load_sequence(SINGLE_ALGS[name], alg_name=name)
        _broadcast_sync({"type": "loaded", "algName": name, "moves": VIEWER_STATE.sequence})
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "animate_sequence":
        moves = parse_sequence(cmd["sequence"])
        VIEWER_STATE.load_sequence(moves, alg_name=None)
        _broadcast_sync({"type": "loaded", "algName": None, "moves": moves})
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "step_forward":
        VIEWER_STATE.step_forward()
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "step_backward":
        VIEWER_STATE.step_backward()
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "goto_move":
        VIEWER_STATE.rewind_to(int(cmd["n"]))
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "reset":
        VIEWER_STATE.reset()
        _broadcast_sync({"type": "reset"})
        _broadcast_sync(VIEWER_STATE.state_snapshot())
    elif t == "get_library":
        return {"ok": True, "library": get_library()}
    elif t == "get_state":
        snap = VIEWER_STATE.state_snapshot()
        snap["ok"] = True
        return snap
    else:
        raise ValueError(f"Unknown command type: {t!r}")
    return {"ok": True}


def _broadcast_sync(msg: dict) -> None:
    if _WS_LOOP and not _WS_LOOP.is_closed():
        future = asyncio.run_coroutine_threadsafe(VIEWER_STATE.broadcast(msg), _WS_LOOP)
        try:
            future.result(timeout=2.0)
        except Exception:
            pass


# ── HTTP ──────────────────────────────────────────────────────────────────────

class _HTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(VIEWER_DIR), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_POST(self) -> None:
        if self.path != "/api/command":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
            result = _handle_command(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except (ValueError, KeyError) as exc:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(exc)}).encode())

    def log_message(self, *_args) -> None:
        pass


def _run_http() -> None:
    server = HTTPServer(("localhost", HTTP_PORT), _HTTPHandler)
    server.serve_forever()


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    """Start HTTP thread + WebSocket asyncio server. Blocks until interrupted."""
    http_thread = threading.Thread(target=_run_http, daemon=True)
    http_thread.start()
    print(f"Viewer:  http://localhost:{HTTP_PORT}/")
    print(f"WS:      ws://localhost:{WS_PORT}/")
    asyncio.run(_run_ws())


if __name__ == "__main__":
    run()
