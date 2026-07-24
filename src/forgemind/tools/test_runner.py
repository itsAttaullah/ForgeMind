"""Run project tests inside the workspace."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from forgemind.core.enums import Permission, RiskClass
from forgemind.core.tools import ToolManifest, ToolParameterSchema
from forgemind.tools.base import BaseTool
from forgemind.tools.repo._paths import workspace_root_or_raise

DEFAULT_TIMEOUT_SECONDS = 60.0


class RunTestsTool(BaseTool):
    """Execute pytest (or a custom command) inside the workspace root."""

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace_root = workspace_root_or_raise(workspace_root)

    @property
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            name="test.run",
            description="Run tests in the workspace (pytest by default).",
            risk_class=RiskClass.EXEC,
            permissions=[Permission.TEST_RUN],
            parameters=ToolParameterSchema(
                type="object",
                properties={
                    "selector": {
                        "type": "string",
                        "description": "Optional pytest node id / path selector.",
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "description": "Process timeout (default: 60).",
                    },
                    "max_output_chars": {
                        "type": "integer",
                        "description": "Truncate combined output to this many chars.",
                    },
                },
                required=[],
                additional_properties=False,
            ),
        )

    async def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        selector = arguments.get("selector")
        timeout = float(arguments.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
        max_chars = int(arguments.get("max_output_chars", 8000))
        if timeout <= 0:
            raise ValueError("timeout_seconds must be > 0")

        command = [sys.executable, "-m", "pytest", "-q"]
        if isinstance(selector, str) and selector.strip():
            command.append(selector.strip())

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(self._workspace_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            process.kill()
            await process.communicate()
            return {
                "passed": False,
                "timed_out": True,
                "exit_code": None,
                "command": command,
                "stdout": "",
                "stderr": f"test run timed out after {timeout}s",
            }

        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")
        exit_code = process.returncode if process.returncode is not None else 1
        return {
            "passed": exit_code == 0,
            "timed_out": False,
            "exit_code": exit_code,
            "command": command,
            "stdout": stdout[:max_chars],
            "stderr": stderr[:max_chars],
            "output_truncated": len(stdout) > max_chars or len(stderr) > max_chars,
        }
