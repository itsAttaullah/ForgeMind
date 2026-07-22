"""Retention helpers — keep summaries only, never private CoT."""

from __future__ import annotations

from forgemind.core.memory import WorkingMemory
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.tools import Observation
from forgemind.memory.budget import DEFAULT_MEMORY_BUDGET, MemoryBudget

# Keys that must never be persisted into working/long-term memory.
_FORBIDDEN_METADATA_KEYS = {
    "chain_of_thought",
    "cot",
    "private_cot",
    "scratchpad",
    "hidden_reasoning",
    "raw_thinking",
}


def sanitize_metadata(metadata: dict[str, object]) -> dict[str, object]:
    """Drop private/CoT metadata keys from a mapping."""

    return {
        key: value for key, value in metadata.items() if key.lower() not in _FORBIDDEN_METADATA_KEYS
    }


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate ``text`` to ``max_chars``, appending an ellipsis when needed."""

    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3].rstrip() + "..."


def sanitize_observation(
    observation: Observation,
    *,
    budget: MemoryBudget = DEFAULT_MEMORY_BUDGET,
) -> Observation:
    """Return a summary-safe observation (truncated + sanitized metadata)."""

    return observation.model_copy(
        update={
            "summary": truncate_text(
                observation.summary,
                budget.max_observation_summary_chars,
            ),
            "details": dict(observation.details),
            # details may be large; keep as-is for now but strip forbidden keys
            # from nested metadata-like dicts only at top-level observation fields.
        }
    )


def sanitize_reflection(
    reflection: ReflectionSummary,
    *,
    budget: MemoryBudget = DEFAULT_MEMORY_BUDGET,
) -> ReflectionSummary:
    """Return a summary-only reflection safe for persistence."""

    return reflection.model_copy(
        update={
            "learned": truncate_text(
                reflection.learned,
                budget.max_reflection_learned_chars,
            ),
            "plan_adjustment": (
                truncate_text(reflection.plan_adjustment, budget.max_reflection_learned_chars)
                if reflection.plan_adjustment
                else None
            ),
            "next_hint": (
                truncate_text(reflection.next_hint, budget.max_reflection_learned_chars)
                if reflection.next_hint
                else None
            ),
            "metadata": sanitize_metadata(dict(reflection.metadata)),
        }
    )


def apply_retention(
    memory: WorkingMemory,
    *,
    budget: MemoryBudget = DEFAULT_MEMORY_BUDGET,
) -> WorkingMemory:
    """Apply list caps (keep most recent) and sanitize stored summaries."""

    observations = [sanitize_observation(item, budget=budget) for item in memory.observations][
        -budget.max_observations :
    ]
    reflections = [sanitize_reflection(item, budget=budget) for item in memory.reflections][
        -budget.max_reflections :
    ]

    files = list(dict.fromkeys(memory.files_inspected))[-budget.max_files_inspected :]
    blockers = memory.blockers[-budget.max_blockers :]
    hypotheses = memory.hypotheses[-budget.max_hypotheses :]
    tests = memory.test_summaries[-budget.max_test_summaries :]

    return memory.model_copy(
        update={
            "files_inspected": files,
            "observations": observations,
            "reflections": reflections,
            "blockers": blockers,
            "hypotheses": hypotheses,
            "test_summaries": tests,
            "metadata": sanitize_metadata(dict(memory.metadata)),
        }
    )
