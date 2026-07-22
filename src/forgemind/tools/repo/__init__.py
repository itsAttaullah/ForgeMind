"""Read-only repository tools package."""

from __future__ import annotations

from pathlib import Path

from forgemind.config.models import ForgeMindConfig
from forgemind.policy.engine import PolicyEngine
from forgemind.tools.executor import ToolExecutor
from forgemind.tools.registry import InMemoryToolRegistry
from forgemind.tools.repo.list_structure import ListStructureTool
from forgemind.tools.repo.read_file import ReadFileTool
from forgemind.tools.repo.search import SearchFilesTool


def register_readonly_repo_tools(
    registry: InMemoryToolRegistry,
    *,
    workspace_root: str | Path,
) -> InMemoryToolRegistry:
    """Register built-in read-only repository tools on ``registry``."""

    registry.register(ListStructureTool(workspace_root))
    registry.register(SearchFilesTool(workspace_root))
    registry.register(ReadFileTool(workspace_root))
    return registry


def create_readonly_tooling(
    *,
    workspace_root: str | Path,
    config: ForgeMindConfig,
) -> ToolExecutor:
    """Create a registry + policy executor with read-only repo tools."""

    registry = InMemoryToolRegistry()
    register_readonly_repo_tools(registry, workspace_root=workspace_root)
    policy = PolicyEngine.from_config(config, workspace_root=workspace_root)
    return ToolExecutor(registry, policy)


__all__ = [
    "ListStructureTool",
    "ReadFileTool",
    "SearchFilesTool",
    "create_readonly_tooling",
    "register_readonly_repo_tools",
]
