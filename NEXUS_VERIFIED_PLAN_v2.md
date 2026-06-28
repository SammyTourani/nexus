# NEXUS v2.0 — Verified Build Plan
### Research synthesis as of June 28, 2026
### Status: AWAITING USER APPROVAL — No build starts until approved

---

## 1. VERDICT ON THE ORIGINAL SPEC

The January 2026 spec had the right instinct (local macOS agent) but three category errors that would cause it to fail in production. These are not opinions — they are verifiable against public benchmarks and macOS system behavior.

### Claim-by-claim audit

| Spec Claim | Verdict | Real Number / Reason |
|---|---|---|
| "No special permissions needed — just screenshot + mouse/keyboard" | **FALSE** | Requires TCC Screen Recording (kTCCServiceScreenCapture) AND Accessibility (kTCCServiceAccessibility) — two of macOS's highest-security grants. macOS 26 Tahoe further requires a properly code-signed .app bundle with stable Apple Developer cert. Raw Python scripts only capture the desktop wallpaper. |
| "88-94% success rate on real workflows" | **FALSE** | Qwen3-VL-235B (the biggest open-source VLM) scores 66.7% on OSWorld. The spec recommends 8B — which scores approximately 35-50%. Human baseline is 72%. No local 8B model has ever exceeded 67% on full OSWorld task completion. |
| "98% button accuracy" | **MISLEADING** | ScreenSpot (the easy element grounding benchmark) gives Qwen3-VL-8B Instruct ~94.4%. This is element grounding only, not task completion. ScreenSpot-Pro (professional interfaces) drops to ~52-55%. The 98% claim is from a different, easier test. |
| "Vision-only is better than hybrid AX + vision" | **FALSE** | Accessibility API (AX tree) reads a focused Slack/Safari/Finder window in 30-80ms. Pure vision needs 200-400ms screenshot capture + 1-4s model inference + coordinate parsing. AX-first is 10x faster and requires the SAME TCC permission level. The spec frames AX as "high setup complexity" but both require user permission; AX just works better. |
| "1-2 second latency per action" | **PARTIALLY FALSE** | Achievable only for cached, AX-readable actions. Fresh vision-path actions take 3-8s. Multi-step complex tasks (book flight, file expense report) take 45-180s total. |
| "Confidence Level: 1,000,000%" | **RED FLAG** | This phrase signals the spec was written aspirationally, not empirically. It should have said "Confidence: Promising, pending validation." |

### What the spec got right
- PyQt6 Spotlight-style global hotkey UI — excellent approach
- SQLite memory system for task caching — correct and important
- Qwen3-VL-8B as the local vision backbone — correct choice for M-series Macs
- pyautogui for cross-app action execution — correct
- 9-week implementation timeline — realistic (for a solo dev)

---

## 2. CORRECTED ARCHITECTURE (Nexus v2.0)

### Philosophy
Nexus v2.0 preserves the privacy-first local vision core, but adds:
1. AX tree as the **primary** interface (fast, accurate, no model cost)
2. Local Qwen3-VL-8B as **vision fallback** only when AX returns empty
3. Claude Sonnet 4.6 as the **planning brain** (API call, ~$0.01-0.03/task)
4. Claude Haiku 4.5 as the **step verifier** (fast, cheap, catches errors early)

This is the industry consensus "AX-first with vision fallback" pattern that Fazm, OpenClaw, and the macOS26/Agent project all converged on independently in 2026.

### Layer diagram

```
User Input (natural language)
         │
         ▼
┌─────────────────────────────────────┐
│  Claude Sonnet 4.6 (Planning)       │  ← generates step-by-step plan
│  "Go to Chrome > search X > click Y"│    $0.003/1K tokens, 1M ctx
└─────────────────────────────────────┘
         │  (plan steps)
         ▼
┌─────────────────────────────────────┐
│  Execution Engine (per step)        │
│                                     │
│  1. Try AX tree first (30-80ms)    │  ← pyobjc AX walker, native apps
│     ↓ if AX empty                   │
│  2. Qwen3-VL-8B via Ollama         │  ← local, no cloud, 94% grounding
│     (200ms capture + 400-800ms inf) │    vision fallback for Qt/web
│                                     │
│  3. Execute: pyautogui / AppleScript│  ← click, type, scroll, hotkey
└─────────────────────────────────────┘
         │  (result of step)
         ▼
┌─────────────────────────────────────┐
│  Claude Haiku 4.5 (Verifier)       │  ← did it work? retry or continue
│  "Screenshot matches expected state?"│   $0.001/1K tokens, fast
└─────────────────────────────────────┘
         │  (verified success or error)
         ▼
┌─────────────────────────────────────┐
│  SQLite Memory + Task Cache         │  ← cache successful step sequences
│  "Last time I booked flights: ..."  │    ~10x faster on repeat tasks
└─────────────────────────────────────┘
```

### Target performance (realistic, evidence-based)

| Metric | Original Spec Claim | Nexus v2.0 Realistic Target |
|---|---|---|
| Task success (3-5 step) | 88-94% | **70-80%** |
| Task success (8-12 step) | ~88% (implied) | **50-65%** |
| AX-path latency | "1-2s" | **80-200ms** |
| Vision-path latency | "1-2s" | **1-3s** |
| Button grounding accuracy | "98%" | **~94%** (ScreenSpot-Pro: ~52%) |
| Cost per task | "$0 (local)" | **$0.01-0.05** (planning only) |
| Privacy | "100% local" | **Local vision + local AX; cloud for planning only** |

### macOS Tahoe compliance
- Build as a proper `.app` bundle using `py2app` or `briefcase`
- Sign with stable Apple Developer certificate (TeamIdentifier constant across rebuilds)
- `Info.plist` must include `NSScreenCaptureUsageDescription` AND `NSAccessibilityUsageDescription`
- TCC grants: Screen Recording + Accessibility — request on first launch
- Never run pyautogui/screencapture from a LaunchAgent or subprocess wrapper (TCC tracks responsible process, not parent)

---

## 3. WHAT WE'RE BUILDING

Three deliverables, produced using G-stack roles and loop engineering:

### Deliverable 1: nexus-app (the product)
A macOS automation agent for Apple Silicon Macs.

**Tech stack:**
- Python 3.12 (M-series optimized)
- PyQt6 (UI — Spotlight-style command bar)
- pyobjc (AX tree walker, native macOS APIs)
- Ollama + Qwen3-VL-8B (local vision inference)
- Anthropic API — Sonnet 4.6 (planning) + Haiku 4.5 (verification)
- pyautogui (click/type/scroll execution)
- SQLite + sqlalchemy (memory and task cache)
- py2app or briefcase (.app bundle packaging)

**File structure:**
```
nexus-app/
├── nexus/
│   ├── core/
│   │   ├── ax_tree.py       # AX tree walker via pyobjc
│   │   ├── vision.py        # Qwen3-VL-8B via Ollama
│   │   ├── planner.py       # Claude Sonnet 4.6 planning
│   │   ├── verifier.py      # Claude Haiku 4.5 step verification
│   │   ├── executor.py      # pyautogui action execution
│   │   └── memory.py        # SQLite task cache
│   ├── ui/
│   │   ├── spotlight.py     # PyQt6 Spotlight-style window
│   │   └── dashboard.py     # Task history + status
│   └── main.py              # Entry point, hotkey registration
├── tests/
│   ├── test_ax_tree.py
│   ├── test_vision.py
│   └── test_e2e.py          # End-to-end: Safari, TextEdit, Finder
├── resources/
│   ├── Info.plist            # TCC usage descriptions
│   └── entitlements.plist
├── setup.py                  # py2app config for .app bundle
├── requirements.txt
└── CLAUDE.md                 # G-stack config + project context
```

**6 loop engineering goals (Claude Code /goal):**
1. "AX tree reads button titles in Safari, TextEdit, and Finder" — done when 3 integration tests pass
2. "Vision fallback identifies UI elements in YouTube and Figma web apps" — done when 2 web tests pass
3. "Planner generates correct 3-step action plans for common tasks" — done when 5 planner unit tests pass
4. "Verifier correctly detects success/failure from screenshots" — done when 4 verification tests pass
5. "Spotlight window opens on cmd+ctrl+space and accepts commands" — done when UI smoke test passes
6. "End-to-end: 'Search Google for AI news and open the first result' completes" — done when e2e test passes

### Deliverable 2: nexus-web (website + landing page)
A single Next.js 15 app that serves as both the product website and landing page.

**Tech stack:**
- Next.js 15 + React 19 (App Router)
- Tailwind CSS v4
- Framer Motion (animations)
- Static export for GitHub Pages / Vercel hosting

**Pages:**
- `/` — Hero landing page (above-the-fold conversion)
- `/about` — What Nexus is, honest capability expectations
- `/docs` — Setup guide, permissions, first task
- `/download` — Release assets, system requirements

**Loop engineering goal:**
- "/goal: Landing page scores 90+ Lighthouse performance and has a working download button"

### Deliverable 3: nexus-docs (embedded in nexus-web)
Full user documentation for setup, first run, troubleshooting TCC permissions.

---

## 4. G-STACK INTEGRATION

G-stack (`github.com/garrytan/gstack`) provides 23 Claude Code roles. We use 8 of them for this build:

| Skill | When to run | What it does for Nexus |
|---|---|---|
| `/office-hours` | Before each week's sprint | Clarifies what we're actually building that week |
| `/plan-ceo-review` | After architecture is drafted | Challenges scope, validates the "why Nexus" business case |
| `/plan-eng-review` | After AX tree design is done | Locks module boundaries, catches architectural mistakes |
| `/plan-design-review` | After Spotlight UI mockup | Catches AI slop in the UI, validates native macOS feel |
| `/review` | After each PR | Finds production bugs before merge |
| `/qa` | After integration milestones | Opens real macOS apps and tests the agent |
| `/cso` | Before packaging .app | OWASP + STRIDE audit on TCC permission handling |
| `/ship` | After each deliverable | Creates release PR with changelog |

**Install command (run once in Claude Code):**
```
Install gstack: run git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```

---

## 5. LOOP ENGINEERING METHODOLOGY

Loop engineering (named by Addy Osmani, June 2026) = designing the loop that runs agents, instead of hand-typing each prompt.

### Claude Code /goal (shipped v2.1.139, May 12, 2026)
The `/goal` command runs Claude across turns until a verifiable condition you write becomes true. A separate fast evaluator model (not the author model) checks the condition after each turn.

**How we use it for Nexus:**
```
/goal: The nexus AX tree module successfully reads UI elements from a running 
       Safari window, TextEdit window, and Finder window, returning element 
       titles, roles, and click coordinates. Done when: pytest tests/test_ax_tree.py 
       passes with 0 failures and 3/3 app integration tests show results.
```

Claude then works autonomously across turns until the condition is met. We monitor cost (set Haiku 4.5 as the evaluator to keep verification cheap) and stop if it's spinning.

### The five loop engineering primitives (applied to Nexus)
1. **Skills** — G-stack skills define how each role thinks
2. **Connectors** — GitHub (commits), Ollama (local inference), Anthropic API (planning)
3. **Sub-agents** — "One agent writes the code, a different one reviews it" (gstack /review)
4. **Memory** — CLAUDE.md in each project + nexus's own SQLite cache
5. **Goal condition** — The `/goal` stop condition for each milestone

---

## 6. BUILD SEQUENCE

### Phase 0 — Setup (Day 1, 2 hours)
1. Clone G-stack: `git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup`
2. Create `nexus-app/` project folder with CLAUDE.md (G-stack section + project context)
3. Create `nexus-web/` project folder
4. Install dependencies: Python 3.12, pyobjc, PyQt6, Ollama, Qwen3-VL-8B model pull
5. Run `/office-hours` in Claude Code on the nexus-app project
6. Run `/plan-ceo-review` — validate scope and "why build this vs. commercial alternatives"

### Phase 1 — AX Tree Core (Days 2-4)
- Implement `ax_tree.py` — pyobjc walker for NSAccessibility
- Loop goal: "AX tree reads 3 real apps"
- Run `/plan-eng-review` on module design
- Run `/review` on PR

### Phase 2 — Vision Fallback (Days 5-7)
- Implement `vision.py` — Qwen3-VL-8B via Ollama REST API
- Set-of-marks overlays for element identification
- Loop goal: "Vision fallback works on YouTube and Figma"
- Run `/review` on PR

### Phase 3 — Planning + Verification (Days 8-10)
- Implement `planner.py` — Claude Sonnet 4.6 via Anthropic API
- Implement `verifier.py` — Claude Haiku 4.5 step verification
- Loop goal: "Planner generates 5 correct action plans; verifier catches 4/4 injected failures"
- Run `/review` on PR

### Phase 4 — Execution + Memory (Days 11-13)
- Implement `executor.py` — pyautogui + AppleScript bridge
- Implement `memory.py` — SQLite task cache
- Loop goal: "End-to-end: 3 simple 3-step tasks complete successfully"
- Run `/qa` — opens real apps and runs the agent

### Phase 5 — UI + Packaging (Days 14-16)
- Implement `spotlight.py` — PyQt6 Spotlight window + global hotkey
- Build `.app` bundle with py2app, code-sign with Apple Developer cert
- Handle TCC permission request flow on first launch
- Loop goal: "App installs, opens on cmd+ctrl+space, executes one task end-to-end"
- Run `/plan-design-review` on UI
- Run `/cso` security audit on TCC handling

### Phase 6 — Website (Days 17-19)
- Build `nexus-web/` Next.js app
- Hero page, about, docs, download
- Loop goal: "Landing page scores 90+ Lighthouse, download link works"
- Run `/qa` on staging URL
- Run `/ship` — release PR

### Phase 7 — Polish + Release (Day 20-21)
- Run `/retro` — review what worked, what didn't
- Final `/review` on all code
- `/document-release` — generate changelog + user docs
- Tag v0.1.0 release
- Deploy website to Vercel

---

## 7. WHAT THIS CANNOT DO (honest scope)

Nexus v2.0, even with the corrected architecture, will NOT:
- Achieve 88-94% on arbitrary complex tasks — realistic is 70-80% on 3-5 step workflows
- Work offline for complex planning (needs Anthropic API for the planning brain)
- Handle enterprise auth flows (SSO, 2FA, Okta) without special logic
- Run reliably on macOS Tahoe without the .app bundle + code signature
- Outperform Qwen3-VL-235B on professional UI grounding (ScreenSpot-Pro ~52%)
- Replace commercial alternatives like OpenClaw for professional use

This is a v0.1.0 that proves the architecture and gives real users something to try. The OSWorld benchmark gap between local 8B and frontier closes further every 6 months.

---

## 8. KEY DECISIONS REQUIRING USER INPUT

Before building starts, confirm:

1. **API key scope:** The plan uses Claude Sonnet 4.6 and Haiku 4.5 via Anthropic API for planning + verification. This is ~$0.01-0.05/task — cheap but not $0. Is this acceptable, or should we attempt a fully-local planning model instead (lowers accuracy to ~50-60%)?

2. **Target macOS version:** The spec says "macOS 13+." macOS Tahoe (26.x) requires stricter .app bundle handling. Should we target Tahoe as the minimum, or support Sequoia 15.x+ as the minimum for a larger install base?

3. **Apple Developer account:** Code-signing the .app requires an Apple Developer account ($99/year). Do you have one? If not, we can build for local dev/sideload only (Gatekeeper bypass required by users).

4. **Website hosting:** Vercel (free tier), GitHub Pages, or self-hosted?

5. **G-stack install:** Do you want to install G-stack globally now, or only install it project-by-project?

---

## APPROVAL GATE

This plan is the result of:
- Reading the full original Nexus spec (6,000+ words)
- Verifying every major claim against 2026 public benchmarks
- Researching macOS Tahoe TCC behavior
- Confirming G-stack structure and loop engineering methodology
- Cross-referencing architecture against 5 independent macOS agent projects (Fazm, OpenClaw, macOS26/Agent, peakmojo/macos-visual-agent, Screen2AX)

**Reply with APPROVED (plus answers to the 5 questions above) to begin the build.**
**Or reply with changes and I'll update the plan before we start.**
