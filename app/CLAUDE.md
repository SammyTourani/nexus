# NEXUS — AI Automation Agent for macOS

## What this is
A local macOS automation agent that uses natural language to control your computer.
Architecture: AX tree (primary, 30-80ms) → Qwen3-VL-8B via Ollama (vision fallback) → Claude Sonnet 4.6 (planning) → Claude Haiku 4.5 (step verification).

## Key files
- `nexus/core/ax_tree.py` — macOS Accessibility API walker (pyobjc)
- `nexus/core/vision.py` — Local Qwen3-VL-8B vision inference via Ollama
- `nexus/core/planner.py` — Claude Sonnet 4.6 task planning
- `nexus/core/verifier.py` — Claude Haiku 4.5 step verification
- `nexus/core/executor.py` — Action execution (pyautogui + AppleScript)
- `nexus/core/memory.py` — SQLite task cache (SQLAlchemy)
- `nexus/ui/spotlight.py` — PyQt6 Spotlight-style command window
- `nexus/ui/dashboard.py` — Task history panel
- `nexus/main.py` — Entry point, global hotkey, lifecycle

## Environment
- Python 3.12, Apple Silicon (M1+), macOS 14 Sonoma+
- Run: `cp .env.example .env` → add ANTHROPIC_API_KEY → `pip install -e .` → `python -m nexus`
- Test: `pytest tests/`

## TCC permissions required
1. System Settings > Privacy & Security > Screen Recording → enable Nexus
2. System Settings > Privacy & Security > Accessibility → enable Nexus

## gstack

/office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review, /design-consultation, /design-shotgun, /design-html, /review, /ship, /land-and-deploy, /canary, /benchmark, /browse, /connect-chrome, /qa, /qa-only, /design-review, /setup-browser-cookies, /setup-deploy, /setup-gbrain, /retro, /investigate, /document-release, /document-generate, /codex, /cso, /autoplan, /plan-devex-review, /devex-review, /careful, /freeze, /guard, /unfreeze, /gstack-upgrade, /learn

Use /browse for all web browsing. Never use mcp__claude-in-chrome__* tools.

## Architecture decisions
- AX tree MUST be tried first before any vision call — it's 10x faster
- Vision fallback fires only when AX returns 0 actionable elements
- Planning happens once per task (not per step) — pass full step list to executor
- Haiku 4.5 verifies EVERY step before moving to the next
- SQLite cache key: SHA256 of (task_description + screen_hash)
- Global hotkey: Cmd+Ctrl+Space (avoids conflict with system Spotlight)
- The .app bundle must be ad-hoc signed: `codesign --sign - Nexus.app`
