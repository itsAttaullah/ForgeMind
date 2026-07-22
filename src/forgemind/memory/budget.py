"""Memory budget and retention settings."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MemoryBudget(BaseModel):
    """Caps for what can be retained and injected into model context."""

    model_config = ConfigDict(extra="forbid")

    max_observations: int = Field(default=50, ge=1)
    max_reflections: int = Field(default=20, ge=1)
    max_files_inspected: int = Field(default=100, ge=1)
    max_blockers: int = Field(default=20, ge=1)
    max_hypotheses: int = Field(default=20, ge=1)
    max_test_summaries: int = Field(default=20, ge=1)
    max_long_term_items: int = Field(default=5, ge=0)
    max_observation_summary_chars: int = Field(default=500, ge=1)
    max_reflection_learned_chars: int = Field(default=1000, ge=1)


DEFAULT_MEMORY_BUDGET = MemoryBudget()
