# Coursera Playwright Automation

Steps to set up and run the Coursera automation workflow.

## 1. Install Dependencies

Ensure Python $\ge 3.14$ and [uv](https://docs.astral.sh/uv/) are installed, then install dependencies and Playwright Chromium:

```bash
uv sync
uv run playwright install chromium
```

## 2. Configuration

Create your `.env` configuration from the example template:

```bash
cp .env.example .env
```

Configure global settings and API keys in `.env`:

```ini
GROQ_API_KEY="gsk_your_groq_api_key"
GROQ_MODEL="openai/gpt-oss-120b"
OPENROUTER_API_KEY="sk-or-v1-your-openrouter-key"
```

### Course Instances Configuration (`instances.py`)

Define your Coursera accounts, passwords, and courses in `instances.py`:

```python
from coursera_automation.instances import InstanceConfig

INSTANCES: list[InstanceConfig] = [
    InstanceConfig(
        email="your_email@example.com",
        password="your_password",
        course_url="https://www.coursera.org/specializations/your-course-url",
        headless=False,
        max_items=50,
    ),
]
```

You can define multiple instances to run concurrent browser sessions in parallel, or easily comment out instances using `#`.

## 3. Run Automation

Execute the automation runner:

```bash
uv run python -m coursera_automation.main
```

## 4. Quality & Verification Checks

Run the verification loop:

```bash
uv run ruff check --fix
uv run ty check
uv run pytest
```

---

For architectural details, sequence diagrams, and module breakdowns, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

