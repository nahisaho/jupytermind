"""TDD verification gate configuration.

Implements DES-AIDS-011 (REQ-AIDS-013): reads the musubix3 project
configuration to confirm the required pytest command the gate depends on
is correctly declared, so the gate can enforce a zero-failure pytest suite
before any implementation change is considered complete.
"""

from __future__ import annotations

import json
from pathlib import Path


class TestCommandMissingError(ValueError):
    """Raised when no required "test" command is declared in the config."""


# @id CODE-AIDS-013
# @implements REQ-AIDS-013
# @design DES-AIDS-011
def get_required_test_command(config_path: str = ".musubix/config.json") -> dict:
    """Return the required "test" command entry from ``config_path``."""
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    for command in config.get("commands", []):
        if command.get("name") == "test":
            if not command.get("required"):
                raise TestCommandMissingError(
                    "The 'test' command is declared but not marked required."
                )
            return command
    raise TestCommandMissingError("No required 'test' command declared in config.")
