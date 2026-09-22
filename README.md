# Coursera Playwright Automation

Automated workflow for logging into Coursera, navigating to courses, resuming progress, and progressing through learning items using Playwright and `uv`.

## Supported Learning Items

| Item | Automated Behavior |
|---|---|
| **Video** | Checks if unmuted and mutes audio (`button[aria-label="Mute"]` and `v.muted = true`); checks if already $2\times$ speed before switching; handles in-video questions by clicking "Skip"; waits exact `duration / 2.0` seconds plus a 6-second completion buffer |
| **Lab** | Scrolls to bottom, checks Honor Code agreement checkbox (`[aria-label="Coursera Honor Code"]`), launches app if available in background, and clicks "Mark as completed" (`data-testid="mark-complete"`) |
| **Reading** | Scrolls through content, clicks "Mark as completed" (`data-testid="mark-complete"`), skips if already completed, and advances |
| **Dialogue / Roleplay** | Clicks "Use text chat" $\to$ "Start Role Play" $\to$ "End Role Play" $\to$ confirms "Yes, end the Role Play" modal and advances |
| **Discussion** | Types `"ok"` into chatbox, clicks "Reply", waits 10s for post registration, and advances |
| **Quiz** | Queries OpenRouter LLM (`poolside/laguna-s-2.1:free`) with reasoning enabled via `requests` and `tenacity` retry backoff (3 attempts, 2-10s exponential backoff); aborts without submitting if answers cannot be obtained; checks honor code agreement, submits, confirms modal, polls for `TopBannerCTAButton` ("Next item") with periodic reload on pending evaluation, and clicks to advance |

## Anti-Bot Stealth & Evasion

Integrates `playwright-stealth` and Chromium flags (`--disable-blink-features=AutomationControlled`, `ignore_default_args=["--enable-automation"]`) across all persistent browser contexts to mask automation fingerprints, avoid Arkose challenge escalation, and maintain clean browser sessions.

## Multi-Instance Execution

Support for running multiple instances concurrently in parallel via `instances.json`:
```json
[
  {
    "email": "user@example.com",
    "password": "Password123!",
    "course_url": "https://www.coursera.org/specializations/generative-ai-for-software-developers",
    "headless": false,
    "max_items": 50
  }
]
```

All instances execute concurrently in parallel using Python's `ThreadPoolExecutor`. If `instances.json` is omitted, the automation falls back to the single default instance in `.env` / `config.py`. See `instances.example.json`.

## Persistent Browser Sessions

Automation uses Playwright's `launch_persistent_context` stored in `.browser_data/<user>_<course_slug>/`. Each concurrent instance maintains an isolated profile directory, ensuring no lock contention or session clashes. Cookies, local storage, and authentication tokens are preserved across runs, allowing subsequent executions to bypass the login modal and Arkose puzzle verification entirely.

## Dialog & Popup Management

`coursera_automation/items/navigation/dialogs.py` automatically dismisses:
- Pendo guides and modals (e.g. "Today's Goals have moved" popup) via `add_locator_handler` and close/confirm triggers
- Transient marketing/help dialogues (`Got it`, close icons)
- Feature announcements (e.g. "We added sound effects" popup cross icon)
- Coursera Honor Code modal (`HonorCodeModal` with "Continue" button)
- Quiz attempt limit warnings (`StartAttemptModal` with "Continue" button)
- End-screen video cards and bottom-bar next buttons

## Architecture Overview

Strictly adheres to NASA JPL Rule 4 (≤ 60 lines per module) organized into domain subpackages:
- `coursera_automation/config.py`: Environment configuration and credentials.
- `coursera_automation/auth.py`: Authentication steps with manual Arkose puzzle wait.
- `coursera_automation/instances.py`: Multi-instance configuration loader and fallback.
- `coursera_automation/course.py`: Specialization navigation & course entry.
- `coursera_automation/main.py`: Browser orchestration for single and multi-instance runs.
- `coursera_automation/items/dispatcher.py`: Item detection and progression iteration loop.
- **Content Subpackage (`items/content/`)**:
  - `video.py`: Video playback, automatic muting, exact 2x duration wait, and 6s buffer.
  - `reading.py`: Progressive scrolling, completion check, and `data-testid="mark-complete"` interaction.
  - `lab.py`: Lab agreement, bottom scroll, and background app launch.
- **Interactive Subpackage (`items/interactive/`)**:
  - `dialogue.py`: Roleplay / dialogue start, text chat mode, end, and confirmation.
  - `discussion.py`: Discussion response input with 10s wait buffer.
- **Navigation Subpackage (`items/navigation/`)**:
  - `navigator.py`: Resume and next item progression navigation with direct href fallback.
  - `dialogs.py`: Pendo guide, honor code, and transient dialog dismissal.
- **Quiz Subpackage (`items/quiz/`)**:
  - `coordinator.py`: Complete quiz lifecycle orchestration.
  - `parser.py`: Question DOM extraction and classification.
  - `solver.py`: OpenRouter LLM API integration with `requests` and `tenacity` retry backoff.
  - `status.py`: Completed/passed quiz and review-mode detection.
  - `submit.py`: Quiz submission and confirmation dialog handling.
  - `poll.py`: 'TopBannerCTAButton' ("Next item") polling with interval logging and reload on pending evaluation.

## Usage & Quality Gates

Run automation:
```bash
uv run python -m coursera_automation.main
```

Verification:
```bash
uv run ruff check --fix
uv run ty check
uv run pytest
```
