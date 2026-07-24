"""Helpers for summarizing workspace changes for the reviewer."""

from __future__ import annotations

from typing import Any

from forgemind.core.memory import WorkingMemory
from forgemind.core.report import ChangedFile


def build_diff_summary(working: WorkingMemory) -> str:
    """Build a compact change summary from working-memory observations."""

    lines: list[str] = []
    changed = infer_changed_files(working)
    if changed:
        lines.append("Changed files:")
        for item in changed:
            rationale = f" ({item.rationale})" if item.rationale else ""
            lines.append(f"- {item.change_type}: {item.path}{rationale}")
    else:
        lines.append("Changed files: (none recorded)")

    if working.test_summaries:
        lines.append("Test results:")
        for summary in working.test_summaries[-5:]:
            lines.append(f"- {summary}")
    else:
        lines.append("Test results: (none recorded)")

    write_obs = [
        obs.summary
        for obs in working.observations
        if obs.source.startswith(("tool:repo.write_file", "tool:repo.edit_file"))
    ]
    if write_obs:
        lines.append("Recent write/edit outcomes:")
        for summary in write_obs[-5:]:
            lines.append(f"- {summary}")

    return "\n".join(lines)


def infer_changed_files(working: WorkingMemory) -> list[ChangedFile]:
    """Infer touched files from write/edit tool observations."""

    changed: list[ChangedFile] = []
    seen: set[str] = set()
    for obs in working.observations:
        if not obs.source.startswith(("tool:repo.write_file", "tool:repo.edit_file")):
            continue
        if "denied" in obs.summary.lower() or "failed" in obs.summary.lower():
            continue
        path = _path_from_observation(obs.details)
        if path is None or path in seen:
            continue
        seen.add(path)
        change_type = "created" if "write_file" in obs.source else "modified"
        changed.append(
            ChangedFile(
                path=path,
                change_type=change_type,
                rationale=obs.summary,
            )
        )
    return changed


def _path_from_observation(details: dict[str, Any]) -> str | None:
    output = details.get("output")
    if isinstance(output, dict):
        path = output.get("path")
        if isinstance(path, str) and path.strip():
            return path
    path = details.get("path")
    if isinstance(path, str) and path.strip():
        return path
    return None
