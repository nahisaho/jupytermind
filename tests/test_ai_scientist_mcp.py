"""Tests for ai_scientist MCP configuration and routing."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_handle(tmp_path, monkeypatch, project_name: str = "mcp-study"):
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(tmp_path / "projects"))
    from ai_scientist.project_handle import resolve_research_project

    return resolve_research_project(project_name)


def _write_unhealthy_managed_server(script_path: Path) -> None:
    script_path.write_text(
        "\n".join(
            [
                "from http.server import BaseHTTPRequestHandler, HTTPServer",
                "import argparse",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--port', type=int, required=True)",
                "args = parser.parse_args()",
                "class Handler(BaseHTTPRequestHandler):",
                "    def do_GET(self):",
                "        self.send_response(404)",
                "        self.end_headers()",
                "    def log_message(self, *_args):",
                "        return",
                "HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()",
            ]
        ),
        encoding="utf-8",
    )


class _FakeMcpClient:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def call_tool(self, tool_name: str, args: dict) -> dict:
        self.calls.append((tool_name, args))
        return {"content": f"results for {tool_name}", "tool": tool_name, "args": args}


@contextmanager
def _external_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):  # noqa: N802
            if self.path != "/tool":
                self.send_response(404)
                self.end_headers()
                return
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            body = json.dumps({"content": f"external:{payload['tool']}"})
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *_args):  # pragma: no cover - quiet test server
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()


# @id TEST-AISCI-015
# @verifies REQ-AISCI-015
def test_TEST_AISCI_015_routes_literature_lookup_through_mcp_client_only(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch)
    fake_client = _FakeMcpClient()

    from ai_scientist.literature_review import handle_literature_review
    from ai_scientist.mcp_gateway import McpGateway

    original_create_connection = socket.create_connection

    def fail_direct_network(*args, **kwargs):
        raise AssertionError(f"unexpected direct network call: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", fail_direct_network)

    gateway = McpGateway(clients={"literature": fake_client})
    result = handle_literature_review(
        handle,
        "Search the latest oncology literature.",
        gateway=gateway,
        server_name="literature",
        tool_name="literature-search",
        tool_args={"query": "oncology"},
    )

    monkeypatch.setattr(socket, "create_connection", original_create_connection)

    assert fake_client.calls == [("literature-search", {"query": "oncology"})]
    assert "literature" in result["artifact_path"]


# @id TEST-AISCI-037
# @verifies REQ-AISCI-015
def test_TEST_AISCI_037_classifies_unregistered_server_instead_of_raising_keyerror():
    from ai_scientist.mcp_gateway import MCPUnavailableError, McpGateway

    gateway = McpGateway(clients={"literature": _FakeMcpClient()})

    with pytest.raises(MCPUnavailableError) as excinfo:
        gateway.call_tool(
            "unregistered-server", "literature-search", {"query": "x"}, phase="literature"
        )

    assert excinfo.value.server_name == "unregistered-server"
    assert excinfo.value.phase == "literature"


# @id TEST-AISCI-016
# @verifies REQ-AISCI-016
def test_TEST_AISCI_016_rejects_invalid_mcp_server_configurations(tmp_path):
    from ai_scientist.mcp_config import McpConfigError, load_mcp_config

    cases = [
        (
            {"servers": [{"name": "broken"}]},
            "mode",
        ),
        (
            {
                "servers": [
                    {
                        "name": "managed",
                        "mode": "managed",
                        "endpointTemplate": "http://127.0.0.1:{port}",
                        "healthCheckPath": "/health",
                    }
                ]
            },
            "launchCommand",
        ),
        (
            {
                "servers": [
                    {
                        "name": "managed",
                        "mode": "managed",
                        "launchCommand": f"{sys.executable} server.py",
                        "endpointTemplate": "http://127.0.0.1:{port}",
                        "healthCheckPath": "/health",
                    }
                ]
            },
            "{port}",
        ),
        (
            {
                "servers": [
                    {
                        "name": "managed",
                        "mode": "managed",
                        "launchCommand": f"{sys.executable} server.py {{port}}",
                        "endpointTemplate": "http://127.0.0.1:9999",
                        "healthCheckPath": "/health",
                    }
                ]
            },
            "{port}",
        ),
        (
            {
                "servers": [
                    {
                        "name": "managed",
                        "mode": "managed",
                        "launchCommand": f"{sys.executable} server.py {{port}}",
                        "endpointTemplate": "http://127.0.0.1:{port}",
                    }
                ]
            },
            "healthCheckPath",
        ),
        (
            {"servers": [{"name": "external", "mode": "external"}]},
            "endpoint",
        ),
    ]

    for index, (payload, expected_message) in enumerate(cases):
        config_path = tmp_path / f"invalid-{index}.json"
        config_path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(McpConfigError, match=expected_message):
            load_mcp_config(config_path)


# @id TEST-AISCI-038
# @verifies REQ-AISCI-016
def test_TEST_AISCI_038_rejects_duplicate_server_names_instead_of_silently_dropping_one(tmp_path):
    from ai_scientist.mcp_config import McpConfigError, load_mcp_config

    payload = {
        "servers": [
            {"name": "literature", "mode": "external", "endpoint": "https://a.example"},
            {"name": "literature", "mode": "external", "endpoint": "https://b.example"},
        ]
    }
    config_path = tmp_path / "duplicate.json"
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(McpConfigError, match="duplicate"):
        load_mcp_config(config_path)


# @id TEST-AISCI-017
# @verifies REQ-AISCI-017
def test_TEST_AISCI_017_starts_managed_server_on_first_use_and_reuses_pid(tmp_path, monkeypatch):
    handle = _resolve_handle(tmp_path, monkeypatch, "managed-study")
    script_path = tmp_path / "managed_server.py"
    script_path.write_text(
        "\n".join(
            [
                "from http.server import BaseHTTPRequestHandler, HTTPServer",
                "import argparse",
                "import json",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--port', type=int, required=True)",
                "args = parser.parse_args()",
                "class Handler(BaseHTTPRequestHandler):",
                "    def do_GET(self):",
                "        if self.path == '/health':",
                "            self.send_response(200); self.end_headers(); self.wfile.write(b'ok')",
                "        else:",
                "            self.send_response(404); self.end_headers()",
                "    def do_POST(self):",
                "        length = int(self.headers.get('Content-Length', '0'))",
                "        payload = json.loads(self.rfile.read(length).decode('utf-8'))",
                "        body = json.dumps({'content': f\"managed:{payload['tool']}\"}).encode('utf-8')",
                "        self.send_response(200)",
                "        self.send_header('Content-Type', 'application/json')",
                "        self.send_header('Content-Length', str(len(body)))",
                "        self.end_headers()",
                "        self.wfile.write(body)",
                "    def log_message(self, *_args):",
                "        return",
                "HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()",
            ]
        ),
        encoding="utf-8",
    )

    from ai_scientist.mcp_config import load_mcp_config
    from ai_scientist.mcp_managed import ensure_managed_server, stop

    config_path = tmp_path / "mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "name": "managed",
                        "mode": "managed",
                        "launchCommand": (f"{sys.executable} {script_path} --port {{port}}"),
                        "endpointTemplate": "http://127.0.0.1:{port}",
                        "healthCheckPath": "/health",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    entry = load_mcp_config(config_path)["managed"]
    first = ensure_managed_server(entry, timeout_ms=3000)
    second = ensure_managed_server(entry, timeout_ms=3000)
    assert first.pid == second.pid

    stop("managed")


# @id TEST-AISCI-018
# @verifies REQ-AISCI-018
def test_TEST_AISCI_018_connects_to_external_server_without_spawning_process(tmp_path, monkeypatch):
    with _external_server() as endpoint:
        from ai_scientist.mcp_config import load_mcp_config
        from ai_scientist.mcp_external import connect_external_server

        def fail_spawn(*_args, **_kwargs):
            raise AssertionError("external mode must not spawn processes")

        monkeypatch.setattr(subprocess, "Popen", fail_spawn)

        config_path = tmp_path / "external.json"
        config_path.write_text(
            json.dumps(
                {"servers": [{"name": "external", "mode": "external", "endpoint": endpoint}]}
            ),
            encoding="utf-8",
        )

        entry = load_mcp_config(config_path)["external"]
        client = connect_external_server(entry)
        result = client.call_tool("literature-search", {"query": "glioma"})

        assert result["content"] == "external:literature-search"


# @id TEST-AISCI-039
# @verifies REQ-AISCI-018
def test_TEST_AISCI_039_rejects_a_non_external_config_entry(tmp_path):
    from ai_scientist.mcp_config import load_mcp_config
    from ai_scientist.mcp_external import connect_external_server

    config_path = tmp_path / "managed.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "name": "managed",
                        "mode": "managed",
                        "launchCommand": f"{sys.executable} server.py {{port}}",
                        "endpointTemplate": "http://127.0.0.1:{port}",
                        "healthCheckPath": "/health",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    entry = load_mcp_config(config_path)["managed"]

    with pytest.raises(ValueError, match="external"):
        connect_external_server(entry)


# @id TEST-AISCI-031
# @verifies REQ-AISCI-017
def test_TEST_AISCI_031_stops_the_process_when_managed_server_startup_times_out(
    tmp_path, monkeypatch
):
    script_path = tmp_path / "unhealthy_managed_server.py"
    _write_unhealthy_managed_server(script_path)

    from ai_scientist.mcp_config import load_mcp_config
    from ai_scientist.mcp_failures import MCPUnavailableError
    import ai_scientist.mcp_managed as mcp_managed

    spawned: list[subprocess.Popen] = []
    original_popen = subprocess.Popen

    def spy_popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        spawned.append(process)
        return process

    monkeypatch.setattr(mcp_managed.subprocess, "Popen", spy_popen)

    config_path = tmp_path / "managed-timeout.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "name": "managed-timeout",
                        "mode": "managed",
                        "launchCommand": f"{sys.executable} {script_path} --port {{port}}",
                        "endpointTemplate": "http://127.0.0.1:{port}",
                        "healthCheckPath": "/health",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    entry = load_mcp_config(config_path)["managed-timeout"]
    with pytest.raises(MCPUnavailableError):
        mcp_managed.ensure_managed_server(entry, timeout_ms=300)

    assert len(spawned) == 1
    try:
        spawned[0].wait(timeout=2)
    finally:
        if spawned[0].poll() is None:
            spawned[0].kill()
            spawned[0].wait(timeout=2)

    assert spawned[0].poll() is not None


# @id TEST-AISCI-019
# @verifies REQ-AISCI-019
def test_TEST_AISCI_019_reports_unreachable_server_and_phase_without_fabricated_evidence(
    tmp_path, monkeypatch
):
    handle = _resolve_handle(tmp_path, monkeypatch, "mcp-down")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    endpoint = f"http://127.0.0.1:{sock.getsockname()[1]}"
    sock.close()

    from ai_scientist.evidence_registry import query_evidence
    from ai_scientist.literature_review import handle_literature_review
    from ai_scientist.mcp_gateway import MCPUnavailableError, McpGateway
    from ai_scientist.mcp_external import HttpMcpClient

    gateway = McpGateway(clients={"broken-mcp": HttpMcpClient(endpoint)})

    with pytest.raises(MCPUnavailableError) as excinfo:
        handle_literature_review(
            handle,
            "Search the literature.",
            gateway=gateway,
            server_name="broken-mcp",
            tool_name="literature-search",
            tool_args={"query": "glioma"},
        )

    assert excinfo.value.server_name == "broken-mcp"
    assert excinfo.value.phase == "literature-review"
    assert query_evidence(handle, "literature-review") == []


# @id TEST-AISCI-032
# @verifies REQ-AISCI-019
def test_TEST_AISCI_032_attributes_managed_startup_failures_to_the_requesting_phase(
    tmp_path,
):
    script_path = tmp_path / "unhealthy_phase_managed_server.py"
    _write_unhealthy_managed_server(script_path)

    from ai_scientist.mcp_config import load_mcp_config
    from ai_scientist.mcp_failures import MCPUnavailableError
    from ai_scientist.mcp_managed import ensure_managed_server

    config_path = tmp_path / "managed-phase.json"
    config_path.write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "name": "managed-phase",
                        "mode": "managed",
                        "launchCommand": f"{sys.executable} {script_path} --port {{port}}",
                        "endpointTemplate": "http://127.0.0.1:{port}",
                        "healthCheckPath": "/health",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    entry = load_mcp_config(config_path)["managed-phase"]
    with pytest.raises(MCPUnavailableError) as excinfo:
        ensure_managed_server(entry, timeout_ms=300, phase="literature-review")

    assert excinfo.value.phase == "literature-review"
