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

Set your credentials and course URL in `.env`:

```ini
COURSERA_EMAIL="your_email@example.com"
COURSERA_PASSWORD="your_password"
COURSERA_COURSE_URL="https://www.coursera.org/specializations/your-course-url"
OPENROUTER_API_KEY="sk-or-v1-your-openrouter-key"
OPENROUTER_MODEL="inclusionai/ling-3.0-flash-fin:free"
```

### Multi-Instance Configuration (Optional)

To run multiple accounts or courses concurrently in parallel, create `instances.json`:

```bash
cp instances.example.json instances.json
```

Edit `instances.json` with the respective email, password, and course URL per instance.

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

