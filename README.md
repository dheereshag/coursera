# Coursera Playwright Automation

Steps to set up and run the Coursera automation workflow.

## 1. Clone the Repository

Clone the repository and enter the project directory:

```bash
git clone https://github.com/dheereshag/coursera.git
cd coursera
```

## 2. Install Dependencies

> [!IMPORTANT]
> **`uv` is required**: This project relies on [`uv`](https://docs.astral.sh/uv/) for fast package resolution and virtual environment management.
>
> Install `uv` before proceeding:
> - **macOS / Linux**:
>   ```bash
>   curl -LsSf https://astral.sh/uv/install.sh | sh
>   ```
> - **Windows**:
>   ```powershell
>   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
>   ```

Ensure Python $\ge 3.14$ and `uv` are installed, then install dependencies and Playwright Chromium:

```bash
uv sync
uv run playwright install chromium
```

## 3. Configuration

Create your `.env` configuration from the example template:

```bash
cp .env.example .env
```

Configure global settings and API keys in `.env`. By default, `.env.example` is configured with **free tier models** so you can get started immediately with a free OpenRouter key:

```ini
OPENROUTER_API_KEY="sk-or-v1-your-free-openrouter-key"
# Free tier models (Default)
OPENROUTER_MODEL="dots-studio/dots-3-note-preview:free"
OPENROUTER_FALLBACK_MODEL="qwen/qwen3.8-27b:free"
```

#### Optional: For Premium / Paid OpenRouter Accounts
If you have a paid OpenRouter account with credits and want higher performance:

```ini
OPENROUTER_API_KEY="sk-or-v1-your-paid-openrouter-key"
OPENROUTER_MODEL="deepseek/deepseek-v4.1-flash"
OPENROUTER_FALLBACK_MODEL="z-ai/glm-5.3-flash"
```

### Course Instances Configuration (`instances.py`)

Create your instances file from the template:

```bash
cp instances.example.py instances.py
```

Define your Coursera accounts, passwords, and courses in `instances.py`:

```python
from coursera_automation.instances import InstanceConfig

INSTANCES: list[InstanceConfig] = [
    InstanceConfig(
        email="your_email@example.com",
        password="your_password",
        course_url="https://www.coursera.org/specializations/your-course-url",
        legal_name="Your Real Legal Name",
        headless=False,
        max_items=50,
    ),
]
```

> [!NOTE]
> **Legal Name Validation**: `legal_name` is required for Coursera Honor Code quiz submissions and must be set to your actual name (cannot be left as `"Your Legal Name"` or empty) to pass startup validation.

You can define multiple instances to run concurrent browser sessions in parallel, or easily comment out instances using `#`.

## 4. Run Automation

Execute the automation runner:

```bash
uv run python -m coursera_automation.main
```

---

For architectural details, sequence diagrams, and module breakdowns, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

