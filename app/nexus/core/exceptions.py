"""
Custom exception hierarchy for NEXUS.
All recoverable errors subclass NexusError; callers catch specifically.
"""
from __future__ import annotations


class NexusError(Exception):
    """Base class for all NEXUS runtime errors."""


class PermissionDeniedError(NexusError):
    """A required macOS TCC permission has not been granted."""

    def __init__(self, permission_name: str) -> None:
        self.permission_name = permission_name
        super().__init__(
            f"macOS '{permission_name}' permission not granted. "
            f"Open System Settings > Privacy & Security > {permission_name} "
            f"and enable Nexus, then restart."
        )


class ConfigurationError(NexusError):
    """Required configuration is missing or invalid."""


class VisionError(NexusError):
    """Local vision model (Qwen3-VL) failed to produce a usable result."""


class PlannerError(NexusError):
    """Claude Sonnet failed to produce a valid action plan."""


class ExecutorError(NexusError):
    """An action step could not be executed after all retries."""

    def __init__(self, step_action: str, step_target: str, reason: str) -> None:
        self.step_action = step_action
        self.step_target = step_target
        self.reason = reason
        super().__init__(f"Failed to execute {step_action}('{step_target}'): {reason}")


class VerificationError(NexusError):
    """Step verification (Claude Haiku) returned an unrecoverable failure."""


class OllamaNotRunningError(NexusError):
    """Ollama is not running or the required model is not pulled."""

    def __init__(self, host: str, model: str) -> None:
        self.host = host
        self.model = model
        super().__init__(
            f"Cannot reach Ollama at {host} or model '{model}' not pulled. "
            f"Run: ollama serve && ollama pull {model}"
        )
