"""
Central configuration for NEXUS.
All env vars are read once at startup via Config.load().
Modules receive a Config instance rather than reading os.getenv inline.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from nexus.core.exceptions import ConfigurationError


@dataclass(frozen=True)
class Config:
    # Anthropic API
    anthropic_api_key: str
    planner_model: str
    verifier_model: str

    # Ollama / local vision
    ollama_host: str
    vision_model: str

    # Execution behaviour
    max_retries: int
    step_delay_s: float
    verify_every_step: bool

    # Storage
    data_dir: Path

    # Logging
    log_level: str

    @classmethod
    def load(cls, env_file: str = ".env") -> "Config":
        """Load configuration from environment, falling back to .env file."""
        load_dotenv(env_file, override=False)

        data_dir = Path(
            os.getenv(
                "NEXUS_DATA_DIR",
                str(Path.home() / "Library" / "Application Support" / "Nexus"),
            )
        )

        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            planner_model=os.getenv("NEXUS_PLANNER_MODEL", "claude-sonnet-4-6"),
            verifier_model=os.getenv("NEXUS_VERIFIER_MODEL", "claude-haiku-4-5"),
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            vision_model=os.getenv("OLLAMA_VISION_MODEL", "qwen3-vl:8b"),
            max_retries=int(os.getenv("NEXUS_MAX_RETRIES", "3")),
            step_delay_s=float(os.getenv("NEXUS_STEP_DELAY_S", "0.3")),
            verify_every_step=os.getenv("NEXUS_VERIFY_EVERY_STEP", "true").lower() == "true",
            data_dir=data_dir,
            log_level=os.getenv("NEXUS_LOG_LEVEL", "INFO"),
        )

    def validate(self) -> None:
        """Raise ConfigurationError if required fields are missing."""
        if not self.anthropic_api_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY is not set. "
                "Add it to your .env file or export it in your shell."
            )
        if not self.anthropic_api_key.startswith("sk-"):
            raise ConfigurationError(
                f"ANTHROPIC_API_KEY looks malformed (expected 'sk-...'). "
                f"Check your .env file."
            )
