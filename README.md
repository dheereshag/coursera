# Coursera Playwright Automation

Automated workflow for logging into Coursera, navigating to courses, resuming progress, and progressing through learning items using Playwright and `uv`.

## Supported Learning Items

| Item | Automated Behavior |
|---|---|
| **Video** | Checks if already $2\times$ speed before switching; waits exact `duration / 2.0` seconds plus a 6-second completion buffer |
| **Lab** | Checks "I agree" checkbox, clicks "Launch app/lab" in background tab without switching focus |
| **Reading** | Scrolls through content, clicks "Mark as completed" (`data-testid="mark-complete"`), skips if already completed, and advances |
| **Dialogue** | Clicks "Start dialogue" $\to$ "End dialogue" and advances |
| **Discussion** | Types `"ok"` into chatbox, clicks "Reply", and advances |
| **Quiz** | Queries NVIDIA LLM (`z-ai/glm-5.3`) for answers, checks honor code agreement, submits, confirms modal, and advances |

## Multi-Instance Execution

Support for multiple concurrent/sequential instances via `instances.json`:
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


If `instances.json` is omitted, the automation falls back to the single default instance in `.env` / `config.py`. See `instances.example.json`.

## Persistent Browser Sessions

Automation uses Playwright's `launch_persistent_context` stored in `.browser_data/<user>/`. Cookies, local storage, and authentication tokens are preserved across runs, allowing subsequent executions to bypass the login modal and Arkose puzzle verification entirely.

## Dialog & Popup Management

`coursera_automation/items/dialogs.py` automatically dismisses:
- Pendo guides and modals (e.g. "Today's Goals have moved" popup) via `add_locator_handler` and close/confirm triggers
- Transient marketing/help dialogues (`Got it`, close icons)
- Feature announcements (e.g. "We added sound effects" popup cross icon)
- Coursera Honor Code modal (`HonorCodeModal` with "Continue" button)
- End-screen video cards and bottom-bar next buttons

## Architecture Overview

Strictly adheres to NASA JPL Rule 4 (≤ 60 lines per module):
- `coursera_automation/config.py`: Environment configuration and credentials.
- `coursera_automation/auth.py`: Authentication steps with manual Arkose puzzle wait.
- `coursera_automation/instances.py`: Multi-instance configuration loader and fallback.
- `coursera_automation/course.py`: Specialization navigation & course entry.
- `coursera_automation/items/video.py`: Video playback, exact 2x duration wait, and 6s buffer.
- `coursera_automation/items/lab.py`: Lab agreement and background app launch.
- `coursera_automation/items/reading.py`: Progressive scrolling, completion check, and `data-testid="mark-complete"` interaction.
- `coursera_automation/items/dialogue.py`: Dialogue start and finish.
- `coursera_automation/items/discussion.py`: Discussion response input.
- `coursera_automation/items/quiz_solver.py`: NVIDIA LLM API integration.
- `coursera_automation/items/quiz.py`: Quiz interaction, type classification, and submission.
- `coursera_automation/items/dialogs.py`: Pendo guide and transient dialog dismissal.
- `coursera_automation/items/navigator.py`: Resume and next item progression navigation.
- `coursera_automation/items/dispatcher.py`: Item detection and iteration loop.
- `coursera_automation/main.py`: Browser orchestration for single and multi-instance runs.

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
