"""Read-only repository tools package."""

from __future__ import annotations

from pathlib import Path

from forgemind.config.models import ForgeMindConfig
from forgemind.policy.engine import PolicyEngine
from forgemind.tools.executor import ToolExecutor
from forgemind.tools.registry import InMemoryToolRegistry
from forgemind.tools.repo.edit_file import EditFileTool
from forgemind.tools.repo.list_structure import ListStructureTool
from forgemind.tools.repo.read_file import ReadFileTool
from forgemind.tools.repo.search import SearchFilesTool
from forgemind.tools.repo.write_file import WriteFileTool
from forgemind.tools.test_runner import RunTestsTool


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


def register_write_repo_tools(
    registry: InMemoryToolRegistry,
    *,
    workspace_root: str | Path,
) -> InMemoryToolRegistry:
    """Register write/edit repository tools on ``registry``."""

    registry.register(WriteFileTool(workspace_root))
    registry.register(EditFileTool(workspace_root))
    return registry


def register_test_tools(
    registry: InMemoryToolRegistry,
    *,
    workspace_root: str | Path,
) -> InMemoryToolRegistry:
    """Register test execution tools on ``registry``."""

    registry.register(RunTestsTool(workspace_root))
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


def create_standard_tooling(
    *,
    workspace_root: str | Path,
    config: ForgeMindConfig,
) -> ToolExecutor:
    """Create tooling with read, write, and test capabilities."""

    registry = InMemoryToolRegistry()
    register_readonly_repo_tools(registry, workspace_root=workspace_root)
    register_write_repo_tools(registry, workspace_root=workspace_root)
    register_test_tools(registry, workspace_root=workspace_root)
    policy = PolicyEngine.from_config(config, workspace_root=workspace_root)
    return ToolExecutor(registry, policy)


__all__ = [
    "EditFileTool",
    "ListStructureTool",
    "ReadFileTool",
    "RunTestsTool",
    "SearchFilesTool",
    "WriteFileTool",
    "create_readonly_tooling",
    "create_standard_tooling",
    "register_readonly_repo_tools",
    "register_test_tools",
    "register_write_repo_tools",
]
