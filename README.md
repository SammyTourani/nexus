# NEXUS

**Local macOS automation agent — speak a task, watch it happen.**

NEXUS uses a three-layer approach that no existing local agent gets right: the macOS Accessibility tree first (30–80 ms, zero model cost), a local Qwen3-VL-8B vision model as a fallback when the tree is empty, and Claude Sonnet 4.6 for planning and Claude Haiku 4.5 for per-step verification. All screen processing is local. Only task planning hits the API.

```
Press Cmd+Ctrl+Space  →  "Move the three most recent PDFs from Downloads to ~/Receipts"
                      →  done in 4.2 s, all steps verified
```

[![CI](https://github.com/sammytourani/nexus/actions/workflows/ci.yml/badge.svg)](https://github.com/sammytourani/nexus/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![macOS 14+](https://img.shields.io/badge/macOS-14%2B-black.svg)](https://www.apple.com/macos/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## How it works

```
User: "Search Google for quarterly earnings and open the first result"

Planner (Claude Sonnet 4.6) → [
  focus_app("Safari"),
  hotkey("cmd+l"),
  type("quarterly earnings site:sec.gov"),
  hotkey("return"),
  click("first search result link")
]

Per step:
  1. Walk AX tree (30–80 ms) — works on Safari, Mail, Finder, TextEdit ...
  2. If tree empty → Qwen3-VL-8B via Ollama (set-of-marks grounding, ~1 s)
  3. Execute via pyautogui / AppleScript
  4. Verify with Claude Haiku 4.5 — retry if it failed, replan if unrecoverable

Successful step sequence → cached in SQLite
Repeat task → 10× faster
```

### Architecture

```
nexus/
├── core/
│   ├── ax_tree.py      AX tree walker (pyobjc) — primary element finder
│   ├── vision.py       Qwen3-VL-8B via Ollama — vision fallback, set-of-marks
│   ├── planner.py      Claude Sonnet 4.6 — task → action step list
│   ├── verifier.py     Claude Haiku 4.5 — post-step screenshot verification
│   ├── executor.py     Orchestrates AX → vision → pyautogui for each step
│   ├── memory.py       SQLite step cache (SQLAlchemy)
│   ├── screenshot.py   Shared capture utilities (mss + Pillow)
│   ├── config.py       Centralised configuration from env
│   └── exceptions.py   Custom exception hierarchy
├── ui/
│   ├── spotlight.py    PyQt6 command bar (Cmd+Ctrl+Space)
│   └── dashboard.py    Floating task history panel
└── utils/
    ├── permissions.py  TCC permission checker on startup
    └── notify.py       macOS notification on task complete/fail
```

---

## Requirements

| Requirement | Version |
|---|---|
| macOS | 14 Sonoma or later |
| Hardware | Apple Silicon (M1 or later) |
| RAM | 16 GB minimum (32 GB recommended for comfortable inference) |
| Python | 3.12 |
| [Ollama](https://ollama.com) | Latest |
| Anthropic API key | Claude Sonnet 4.6 + Haiku 4.5 |
| Disk | ~5 GB for the Qwen3-VL-8B model |

---

## Quickstart

### 1. Pull the local vision model

```bash
ollama pull qwen3-vl:8b
```

This is a one-time download of ~4.5 GB. NEXUS will warn you if Ollama is not running or the model is missing.

### 2. Clone and install

```bash
git clone https://github.com/sammytourani/nexus.git
cd nexus/app
pip install -e .
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` and set your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

All other values have sane defaults. See `.env.example` for the full list.

### 4. Grant macOS permissions

NEXUS requires two TCC grants. Open each link in your browser or navigate manually:

- **Accessibility**: `System Settings → Privacy & Security → Accessibility` — enable Terminal (for dev) or Nexus.app (for bundled)
- **Screen Recording**: `System Settings → Privacy & Security → Screen Recording` — enable Terminal or Nexus.app

NEXUS checks permissions on startup and exits with a clear message if either is missing.

### 5. Run

```bash
python -m nexus
```

Press **Cmd+Ctrl+Space** to open the command bar. Type your task in plain English. Press Enter.

---

## Configuration reference

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required.** Your Anthropic API key. |
| `NEXUS_PLANNER_MODEL` | `claude-sonnet-4-6` | Model used for task planning. |
| `NEXUS_VERIFIER_MODEL` | `claude-haiku-4-5` | Model used for per-step verification. |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint. |
| `OLLAMA_VISION_MODEL` | `qwen3-vl:8b` | Local vision model name in Ollama. |
| `NEXUS_MAX_RETRIES` | `3` | Retry count per action step before failure. |
| `NEXUS_STEP_DELAY_S` | `0.3` | Seconds to pause between steps. |
| `NEXUS_VERIFY_EVERY_STEP` | `true` | Set to `false` to skip Haiku verification (faster, less reliable). |
| `NEXUS_LOG_LEVEL` | `INFO` | Python log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `NEXUS_DATA_DIR` | `~/Library/Application Support/Nexus` | Where the SQLite database lives. |

---

## Build the .app bundle

No Apple Developer account is required. The bundle is ad-hoc signed; users run a one-time Gatekeeper bypass.

```bash
cd app
pip install ".[bundle]"
python setup.py py2app

# Ad-hoc sign (no developer certificate required)
codesign --sign - --force --deep dist/Nexus.app
```

**Installing for users:**

```bash
cp -r dist/Nexus.app /Applications/

# One-time Gatekeeper bypass (users run this once after download)
sudo xattr -rd com.apple.quarantine /Applications/Nexus.app

open /Applications/Nexus.app
```

---

## Testing

Tests are split into three tiers:

| Tier | Command | Requires |
|---|---|---|
| Unit | `pytest tests/ -m "not integration and not e2e"` | Nothing — all deps mocked |
| Integration | `pytest tests/ -m integration` | Accessibility permission + open apps |
| End-to-end | `pytest tests/ -m e2e` | All permissions + API key + Ollama |

```bash
cd app

# Fast unit tests (CI uses this)
pip install -e ".[dev]"
pytest tests/ -m "not integration and not e2e" -v

# Full integration suite
pytest tests/ -v --timeout=60
```

CI runs unit tests on every push using a macOS 14 Apple Silicon runner.

---

## Performance expectations

These numbers reflect real benchmark data, not spec claims.

| Metric | Target | Notes |
|---|---|---|
| Task success (3–5 steps) | 70–80% | Comparable to Qwen3-VL-235B on OSWorld |
| Task success (8–12 steps) | 50–65% | Multi-app workflows, more failure surface |
| AX-path action | 80–200 ms | Native apps: Safari, Mail, Finder, TextEdit |
| Vision-path action | 1–3 s | Qt apps, web canvas elements, custom renderers |
| Button grounding (ScreenSpot) | ~94% | Qwen3-VL-8B Instruct |
| Repeat task (cached) | ~10× faster | SQLite step cache |
| Cost per task | $0.01–0.05 | Sonnet 4.6 planning + Haiku 4.5 verification |

The AX tree is the fast path. Vision is the fallback. Most interactions on native macOS apps (Finder, Mail, Safari, TextEdit, Calendar, Notes) go through AX and never touch the vision model.

---

## What NEXUS handles well

- Navigation tasks: "Go to my last email from Sarah and archive it"
- File operations: "Move all screenshots from Desktop to Screenshots folder"
- Web tasks: "Search Hacker News for the top AI story today"
- App workflows: "Open the TextEdit document I was working on yesterday"
- Multi-step sequences on native macOS apps

## What it does not handle (v0.1)

- Enterprise SSO / 2FA flows
- Captchas
- Apps with entirely empty accessibility trees and no legible vision targets
- Video streaming UI (e.g., YouTube playback controls during full-screen)
- Tasks requiring persistent background context ("remind me at 3pm")

---

## Repository layout

```
nexus/
├── app/                   Python automation agent
│   ├── nexus/             Package source
│   ├── tests/             Unit + integration + e2e tests
│   ├── resources/         Info.plist for .app bundle
│   ├── pyproject.toml
│   └── setup.py           py2app bundle configuration
├── web/                   Marketing website (Next.js 16, static export)
│   ├── app/               Next.js App Router pages
│   └── components/        Shared React components
├── .github/
│   └── workflows/
│       ├── ci.yml         Python unit tests on push
│       └── deploy-web.yml Deploy web/ to GitHub Pages on push to main
├── LICENSE
└── README.md
```

---

## Contributing

```bash
git clone https://github.com/sammytourani/nexus.git
cd nexus/app
pip install -e ".[dev]"
pytest tests/ -m "not integration and not e2e"  # make sure unit tests pass
```

Write tests for new modules. New core modules should have unit tests that mock external deps (Anthropic API, Ollama, pyobjc). Integration tests should use the `@pytest.mark.integration` marker.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgements

Architecture informed by:
- [Screen2AX](https://arxiv.org/abs/2507.16704) — vision-based AX tree generation
- [OS-Symphony](https://arxiv.org/pdf/2601.07779) — holistic computer-use agent framework
- [MacArena](https://arxiv.org/html/2606.06560) — macOS agent benchmarking
- [fazm.ai](https://fazm.ai/blog/macos-ai-agent) — AX-first macOS agent design patterns
