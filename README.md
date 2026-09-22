# Coursera Playwright Automation

Automated workflow for logging into Coursera, navigating to courses, resuming progress, and progressing through learning items using Playwright and `uv`.

## Supported Learning Items

| Item | Automated Behavior |
|---|---|
| **Video** | Checks if unmuted and mutes audio (`button[aria-label="Mute"]` and `v.muted = true`); checks if already $2\times$ speed before switching; polls every 0.5s for in-video questions to click CDS "Skip", auto-clicks `data-testid="playToggle"` whenever paused; waits exact `duration / 2.0` seconds plus a 6-second completion buffer |


| **Lab** | Scrolls to bottom, checks Honor Code agreement checkbox (`[aria-label="Coursera Honor Code"]` with bounded timeout), launches app if available in background, and clicks "Mark as completed" (`data-testid="mark-complete"`) |
| **Reading** | Checks if already completed; if not, waits unconditional full 60s duration (12 cycles $\times$ 5s) scrolling down 600px, then scrolls to bottom and clicks "Mark as completed" (`data-testid="mark-complete"`), waiting 3s for state persistence |
| **Dialogue / Roleplay** | Clicks "Use text chat" $\to$ "Start Role Play" $\to$ "End Role Play" $\to$ confirms "Yes, end the Role Play" modal and advances |
| **Discussion** | 10-second stabilization wait, opens reply composer if collapsed, types `"ok"`, clicks "Reply", waits 12s, and advances |
| **Peer Assignment** | 10s load wait, selects "My submission" tab, fills title with "test", uploads `test.png` via Uppy file chooser, polls up to 120s for processing, checks Honor Code, submits, confirms modal, and advances |
| **Quiz / Graded Assignment** | Parses single-choice, multiple-choice, and auto-gradable `<textarea>` questions; queries OpenRouter LLM (`poolside/laguna-s-2.1:free`) with reasoning enabled via `requests` and `tenacity` retry backoff (3 attempts, 2-10s exponential backoff); fills textarea inputs and selects options; aborts without submitting if answers cannot be obtained; checks honor code agreement, submits, confirms modal, polls for `TopBannerCTAButton` ("Next item") with periodic reload on pending evaluation, and clicks to advance |


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
- `coursera_automation/keep_awake.py`: macOS sleep prevention power assertion context manager.
- `coursera_automation/course.py`: Specialization navigation & dynamic course entry CTA waiting (up to 40s hydration wait with 1s polling and instant bypass for already-loaded states).
- `coursera_automation/main.py`: Browser orchestration for single and multi-instance runs.
- `coursera_automation/items/dispatcher.py`: Item detection and progression iteration loop.
- **Content Subpackage (`items/content/`)**:
  - `video.py`: Video playback, automatic muting, exact 2x duration wait, and 6s buffer.
  - `reading.py`: Progressive scrolling, completion check, and `data-testid="mark-complete"` interaction.
  - `lab.py`: Lab agreement, bottom scroll, and background app launch.
- **Interactive Subpackage (`items/interactive/`)**:
  - `dialogue.py`: Roleplay / dialogue start, text chat mode, end, and confirmation.
  - `discussion.py`: Discussion response input with 10s wait buffer.
- **Peer Assignment Subpackage (`items/peer/`)**:
  - `coordinator.py`: My submission tab, title input, upload, Honor Code check, submit, and next item advance.
  - `upload.py`: Uppy Dashboard file chooser interaction and direct file input fallback.
- **Navigation Subpackage (`items/navigation/`)**:

  - `navigator.py`: Resume and next item progression navigation with direct href fallback.
  - `dialogs.py`: Pendo guide, honor code, and transient dialog dismissal.
- **Quiz Subpackage (`items/quiz/`)**:
  - `coordinator.py`: Complete quiz lifecycle orchestration with option selection and textarea answer filling.
  - `loader.py`: Progressive scrolling, expected question count detection, and DOM hydration stabilization.
  - `parser.py`: Question DOM extraction, single/multiselect/textarea classification, and aria-labelledby/cml prompt retrieval.
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
