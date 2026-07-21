"""Serialization tests for reports, review, memory, and tools."""

from __future__ import annotations

from forgemind.core import (
    EngineeringReport,
    FindingSeverity,
    MemorySnapshot,
    Observation,
    ReflectionSummary,
    ReflectionVerdict,
    ReviewFinding,
    ReviewReport,
    RunStatus,
    ToolCall,
    ToolManifest,
    ToolResult,
    ToolResultStatus,
    WorkingMemory,
)


def test_tool_result_and_observation_round_trip() -> None:
    call = ToolCall(call_id="c1", tool_name="repo.search", arguments={"query": "JWT"})
    result = ToolResult(
        call_id=call.call_id,
        tool_name=call.tool_name,
        status=ToolResultStatus.SUCCESS,
        output={"matches": ["auth/jwt.py"]},
    )
    observation = Observation(
        source="tool:repo.search",
        summary="Found jwt module",
        details={"matches": result.output},
        related_call_id=call.call_id,
    )
    restored = Observation.model_validate(observation.model_dump(mode="json"))
    assert restored.related_call_id == "c1"


def test_review_report_blocking_findings() -> None:
    report = ReviewReport(
        summary="Needs work",
        findings=[
            ReviewFinding(
                title="Missing authz check",
                severity=FindingSeverity.HIGH,
                detail="Endpoint lacks authorization",
                path="api/routes.py",
            )
        ],
        approve_completion=False,
    )
    assert report.has_blocking_findings
    raw = report.model_dump(mode="json")
    assert ReviewReport.model_validate(raw).findings[0].severity == FindingSeverity.HIGH


def test_memory_and_engineering_report_round_trip() -> None:
    memory = MemorySnapshot(
        working=WorkingMemory(
            task_brief="Add JWT auth",
            observations=[Observation(source="tool:repo.list", summary="Listed top-level files")],
            reflections=[
                ReflectionSummary(
                    verdict=ReflectionVerdict.CONTINUE,
                    helped=True,
                    learned="Auth package already exists",
                )
            ],
        )
    )
    report = EngineeringReport(
        run_id="run-1",
        status=RunStatus.COMPLETED,
        task_restatement="Add JWT authentication",
        key_findings=["Existing session auth can be extended"],
        residual_risks=["Token rotation not implemented"],
    )
    assert MemorySnapshot.model_validate(memory.model_dump(mode="json")).working.task_brief
    assert EngineeringReport.model_validate(report.model_dump(mode="json")).run_id == "run-1"


def test_tool_manifest_defaults() -> None:
    manifest = ToolManifest(name="repo.read_file", description="Read a text file")
    assert manifest.risk_class.value == "read"
    assert manifest.requires_approval is False
