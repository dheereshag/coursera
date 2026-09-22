# Architecture & Design

This project automates Coursera workflows using Playwright in Python, strictly adhering to NASA JPL Rule 4 (≤ 60 lines per module) and the 3-step verification loop.

## Architecture

```mermaid
sequenceDiagram
    autonumber
    participant Main as coursera_automation.main
    participant Inst as coursera_automation.instances
    participant Auth as coursera_automation.auth
    participant Course as coursera_automation.course
    participant Disp as items.dispatcher
    participant Item as Video/Lab/Reading/Quiz/Dialogue/Discussion
    participant LLM as OpenRouter Laguna-2.1
    participant Dial as items.navigation.dialogs
    participant Nav as items.navigation.navigator

    Main->>Inst: load_instances("instances.json")
    Inst-->>Main: list[InstanceConfig]
    par Concurrent Execution (ThreadPoolExecutor)
        Main->>Dial: register_dialog_handlers(page)
        Main->>Auth: login(page, config)
        Main->>Course: open_course(page, config)
        Course->>Nav: click_resume(page, config)
        Course->>Disp: process_items(page, config)
        loop Up to max_items
            Disp->>Dial: dismiss_dialogs(page)
            Disp->>Item: dispatch_item(page, config)
            opt Video Item
                Item->>Item: Mute audio, 2x speed playback & 6s post-buffer
            end
            opt Quiz Item
                Item->>LLM: solve_quiz_with_llm(questions)
                LLM-->>Item: JSON answers
                Item->>Item: Check honor code, submit & confirm modal
                Item->>Item: Poll TopBannerCTAButton ('Next item') & click to advance
            end

            Disp->>Nav: click_next_item(page, config)
        end
    end
```

## Modular Decomposition (NASA JPL Rule 4)

- `coursera_automation/config.py`: Environment configuration and typed dataclass.
- `coursera_automation/instances.py`: Multi-instance configuration loading and single-instance fallback.
- `coursera_automation/keep_awake.py`: macOS sleep prevention power assertion context manager.
- `coursera_automation/auth.py`: Authentication interactions with Arkose puzzle manual solve window.
- `coursera_automation/course.py`: Specialization navigation, resilient multi-state course entry, and dynamic CTA hydration wait (up to 40s).
- `coursera_automation/main.py`: Multi-instance orchestration with `playwright-stealth` anti-bot evasion and keep-awake integration.
- `coursera_automation/items/dispatcher.py`: Top-level item detection and progression iteration loop.
- **Content Subpackage (`items/content/`)**:
  - `video.py`: Video start, audio muting, 2x playback, 0.5s in-video question skip polling, playToggle auto-resume, and 6s post-buffer.


  - `reading.py`: Reading completion via unconditional 60s wait (12 cycles $\times$ 5s scrolling), bottom scroll, and `data-testid="mark-complete"` click.
  - `lab.py`: Lab Honor Code agreement with bounded timeout, bottom scrolling, optional LTI launch, and "Mark as completed".
- **Interactive Subpackage (`items/interactive/`)**:
  - `dialogue.py`: Roleplay / dialogue start, text chat selection, end, and modal confirmation.
  - `discussion.py`: Discussion response input with 10-second post-reply stabilization buffer.
- **Peer Assignment Subpackage (`items/peer/`)**:
  - `coordinator.py`: Peer submission coordination, title, upload wait, Honor Code, submit, and next item progression.
  - `upload.py`: File attachment via Uppy Dashboard file chooser and direct file input fallback.
- **Navigation Subpackage (`items/navigation/`)**:

  - `navigator.py`: Resume / Get started and next item progression navigation with direct `href` fallback.
  - `dialogs.py`: Pendo guide, Honor Code, weekly learning target (Cancel), and transient popup dialog dismissal.
- **Quiz Subpackage (`items/quiz/`)**:
  - `coordinator.py`: Complete quiz lifecycle coordination, option selection, and textarea answer filling.
  - `loader.py`: Progressive scrolling, expected question count detection, and DOM hydration stabilization.
  - `parser.py`: Question DOM extraction, single/multiselect/textarea classification, and aria-labelledby/cml prompt retrieval.
  - `solver.py`: OpenRouter LLM API integration with `requests` and `tenacity` retry backoff.
  - `status.py`: Completed/passed quiz and review-mode detection.
  - `submit.py`: Quiz submission and modal confirmation dialog handling.
  - `poll.py`: 'TopBannerCTAButton' ("Next item") polling with interval logging and reload on pending evaluation.
