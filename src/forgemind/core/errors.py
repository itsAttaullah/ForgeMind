"""Typed error hierarchy for ForgeMind."""

from __future__ import annotations


class ForgeMindError(Exception):
    """Base error for all ForgeMind failures."""


class ValidationError(ForgeMindError):
    """Raised when domain payloads fail schema or invariant checks."""


class InvalidActionError(ValidationError):
    """Raised when an ``AgentAction`` payload is malformed or unsupported."""


class ConfigurationError(ForgeMindError):
    """Raised when configuration cannot be loaded or is inconsistent."""


class PermissionDeniedError(ForgeMindError):
    """Raised when a tool/action violates the active policy."""


class BudgetExceededError(ForgeMindError):
    """Raised when a run exceeds step, time, or cost budgets."""


class ProviderError(ForgeMindError):
    """Raised when a model provider call fails."""


class ToolExecutionError(ForgeMindError):
    """Raised when a tool fails during execution."""


class IllegalTransitionError(ForgeMindError):
    """Raised when a run attempts an illegal state transition."""
