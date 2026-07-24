"""Heuristic and provider-backed reviewers (ADR 0004)."""

from __future__ import annotations

import json
import re
from typing import Any

from forgemind.core.enums import FindingSeverity, MessageRole, RunStatus
from forgemind.core.errors import InvalidActionError, ProviderError
from forgemind.core.memory import MemorySnapshot
from forgemind.core.messages import ChatMessage
from forgemind.core.protocols import ModelProvider
from forgemind.core.provider import ProviderRequest
from forgemind.core.review import ReviewFinding, ReviewReport
from forgemind.core.state import RunState
from forgemind.review.diff import build_diff_summary, infer_changed_files

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class HeuristicReviewer:
    """Rule-based reviewer that emits structured findings (no private CoT)."""

    async def review(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        diff_summary: str,
        focus: list[str] | None = None,
    ) -> ReviewReport:
        findings: list[ReviewFinding] = []
        working = memory.working
        changed = infer_changed_files(working)
        tests_failed = any("fail" in item.lower() for item in working.test_summaries)
        tests_passed = any("pass" in item.lower() for item in working.test_summaries)
        focus = focus or []

        if tests_failed:
            findings.append(
                ReviewFinding(
                    title="Tests still failing",
                    severity=FindingSeverity.HIGH,
                    detail="Latest recorded test summaries include failures.",
                    recommendation="Return to testing after addressing the failing suite.",
                )
            )

        if changed and not working.test_summaries:
            findings.append(
                ReviewFinding(
                    title="Changes without test evidence",
                    severity=FindingSeverity.MEDIUM,
                    detail="Files were modified but no test.run results are recorded.",
                    recommendation="Run tests before completing the task.",
                )
            )

        denied_writes = [
            obs
            for obs in working.observations
            if obs.source.startswith(("tool:repo.write_file", "tool:repo.edit_file"))
            and "denied" in obs.summary.lower()
        ]
        if denied_writes:
            findings.append(
                ReviewFinding(
                    title="Denied write attempts",
                    severity=FindingSeverity.HIGH,
                    detail=denied_writes[-1].summary,
                    recommendation="Do not complete while policy-denied writes remain unresolved.",
                )
            )

        for topic in focus:
            findings.append(
                ReviewFinding(
                    title=f"Focus check: {topic}",
                    severity=FindingSeverity.INFO,
                    detail=f"Reviewer was asked to focus on '{topic}'.",
                    recommendation="Confirm this concern is addressed in the final report.",
                )
            )

        if not changed and not findings:
            findings.append(
                ReviewFinding(
                    title="No code changes detected",
                    severity=FindingSeverity.INFO,
                    detail="Working memory has no successful write/edit observations.",
                    recommendation="Complete only if the task was read-only analysis.",
                )
            )

        blocking = any(
            f.severity in {FindingSeverity.HIGH, FindingSeverity.CRITICAL} for f in findings
        )
        approve = not (
            tests_failed or blocking or (changed and not tests_passed)
        )

        summary = (
            "Review approved with no blocking findings."
            if approve
            else "Review found issues that block completion."
        )
        return ReviewReport(
            summary=summary,
            findings=findings,
            approve_completion=approve,
            metadata={
                "reviewer": "heuristic",
                "diff_summary": diff_summary,
                "changed_file_count": len(changed),
            },
        )


class ProviderReviewer:
    """Ask a model for a JSON ReviewReport, with heuristic fallback."""

    def __init__(self, provider: ModelProvider, *, model: str | None = None) -> None:
        self._provider = provider
        self._model = model
        self._fallback = HeuristicReviewer()

    async def review(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        diff_summary: str,
        focus: list[str] | None = None,
    ) -> ReviewReport:
        prompt = {
            "goal": state.task.goal,
            "status": state.status.value,
            "diff_summary": diff_summary,
            "focus": focus or [],
            "test_summaries": memory.working.test_summaries[-5:],
            "instruction": (
                "Return ONLY JSON ReviewReport with keys: summary, findings, "
                "approve_completion. Each finding needs title, severity "
                "(info|low|medium|high|critical), detail; optional path and "
                "recommendation. Do not include chain-of-thought."
            ),
        }
        try:
            payload = await self._request_json(prompt)
            report = ReviewReport.model_validate(payload)
            metadata = dict(report.metadata)
            metadata["reviewer"] = "provider"
            return report.model_copy(update={"metadata": metadata})
        except (ProviderError, InvalidActionError, ValueError):
            return await self._fallback.review(
                state,
                memory,
                diff_summary=diff_summary,
                focus=focus,
            )

    async def _request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._provider.complete(
            ProviderRequest(
                model=self._model,
                messages=[
                    ChatMessage(
                        role=MessageRole.SYSTEM,
                        content=(
                            "You are the ForgeMind reviewer (separate from the actor). "
                            "Reply with ONLY a JSON ReviewReport. Be critical; do not "
                            "rubber-stamp. Never include private reasoning."
                        ),
                    ),
                    ChatMessage(role=MessageRole.USER, content=json.dumps(payload, default=str)),
                ],
                response_format={"type": "json_object"},
            )
        )
        return _extract_json_object(response.message.content)


def should_block_completion(report: ReviewReport) -> bool:
    """Return True when the review refuses completion."""

    return (not report.approve_completion) or report.has_blocking_findings


def resume_status_after_review(report: ReviewReport, memory: MemorySnapshot) -> RunStatus:
    """Choose Acting vs Testing when review blocks completion."""

    tests_failed = any("fail" in item.lower() for item in memory.working.test_summaries)
    if tests_failed or any(
        "test" in (finding.recommendation or "").lower()
        or "test" in finding.detail.lower()
        for finding in report.findings
        if finding.severity in {FindingSeverity.HIGH, FindingSeverity.CRITICAL}
    ):
        return RunStatus.TESTING
    return RunStatus.ACTING


def default_diff_summary(memory: MemorySnapshot) -> str:
    """Convenience wrapper around ``build_diff_summary``."""

    return build_diff_summary(memory.working)


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        loaded = json.loads(cleaned)
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        match = _JSON_OBJECT_RE.search(cleaned)
        if match:
            loaded = json.loads(match.group(0))
            if isinstance(loaded, dict):
                return loaded
    raise InvalidActionError("provider did not return a JSON ReviewReport object")
