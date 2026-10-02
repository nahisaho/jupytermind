"""MCP server configuration loading for ai_scientist."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class McpConfigError(ValueError):
    """Invalid MCP configuration."""


@dataclass(frozen=True)
class ManagedServerConfig:
    name: str
    mode: str
    launch_command: str
    endpoint_template: str
    health_check_path: str


@dataclass(frozen=True)
class ExternalServerConfig:
    name: str
    mode: str
    endpoint: str


def _require(payload: dict, field: str, server_name: str) -> str:
    value = payload.get(field)
    if not value:
        raise McpConfigError(f"{server_name}: missing required field '{field}'")
    return value


# @id CODE-AISCI-016
# @implements REQ-AISCI-016
# @design DES-AISCI-011
def load_mcp_config(
    config_path: Path | str,
) -> dict[str, ManagedServerConfig | ExternalServerConfig]:
    """Load and validate MCP server entries."""
    payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
    servers = payload.get("servers", [])
    validated: dict[str, ManagedServerConfig | ExternalServerConfig] = {}
    for entry in servers:
        name = _require(entry, "name", "<unnamed>")
        if name in validated:
            raise McpConfigError(f"{name}: duplicate server name")
        mode = _require(entry, "mode", name)
        if mode == "managed":
            launch_command = _require(entry, "launchCommand", name)
            endpoint_template = _require(entry, "endpointTemplate", name)
            health_check_path = _require(entry, "healthCheckPath", name)
            if "{port}" not in launch_command:
                raise McpConfigError(f"{name}: launchCommand must contain '{{port}}'")
            if "{port}" not in endpoint_template:
                raise McpConfigError(f"{name}: endpointTemplate must contain '{{port}}'")
            validated[name] = ManagedServerConfig(
                name=name,
                mode=mode,
                launch_command=launch_command,
                endpoint_template=endpoint_template,
                health_check_path=health_check_path,
            )
            continue
        if mode == "external":
            validated[name] = ExternalServerConfig(
                name=name,
                mode=mode,
                endpoint=_require(entry, "endpoint", name),
            )
            continue
        raise McpConfigError(f"{name}: mode must be 'managed' or 'external'")
    return validated
