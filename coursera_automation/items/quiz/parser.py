"""DOM extraction and question classification for Coursera quizzes."""

from typing import Any

from playwright.sync_api import Error, Locator, Page

Q_SEL = 'fieldset, [role="radiogroup"], [data-testid*="question"], textarea'


def _is_textarea(loc: Locator) -> bool:
    """Check if locator is a textarea element."""
    try:
        return loc.evaluate("el => el.tagName") == "TEXTAREA"
    except (Error, AttributeError):
        return False


def _detect_type(q_loc: Locator) -> str:
    """Classify question as textarea, multiselect, or single."""
    if q_loc.locator("textarea").count() or _is_textarea(q_loc):
        return "textarea"
    return "multiselect" if q_loc.locator('input[type="checkbox"], [role="checkbox"]').count() else "single"


def _extract_prompt(q_loc: Locator) -> str:
    """Extract question prompt from cml-viewer, aria-labelledby, or container."""
    c = q_loc.locator('[data-testid="cml-viewer"]:not(label *)').first
    c = c if c.is_visible(timeout=100) else q_loc.locator('xpath=preceding::div[@data-testid="cml-viewer"][not(ancestor::label)][1]').first
    if not c.is_visible(timeout=100) and (lid := q_loc.get_attribute("aria-labelledby")):
        c = q_loc.page.locator(f'[id="{lid}"]').first
    return str(c.inner_text().strip()) if c.is_visible(timeout=100) else str(q_loc.get_attribute("placeholder") or q_loc.inner_text().strip())


def _find_question_locs(page: Page) -> list[Locator]:
    """Find question locators avoiding parent-child duplicates."""
    locs = [q for q in page.locator('fieldset, [role="radiogroup"], textarea:not(fieldset textarea)').all() if not q.locator("#agreement-checkbox-base").count()]
    return locs or [q for q in page.locator('[data-testid*="question"]').all() if not q.locator("#agreement-checkbox-base").count()]


def wait_and_extract_questions(page: Page, timeout_ms: int) -> tuple[list[Locator], list[dict[str, Any]]]:
    """Wait for quiz questions to load and parse prompts and options."""
    try:
        page.locator(Q_SEL).first.wait_for(state="attached", timeout=timeout_ms)
    except Error:
        pass

    q_locs: list[Locator] = []
    for _ in range(10):
        q_locs = _find_question_locs(page)
        if q_locs and any(q.locator("label, input, textarea").all() or _is_textarea(q) for q in q_locs):
            break
        page.wait_for_timeout(1000)

    questions = [
        {"index": i, "question": _extract_prompt(q), "options": [o.inner_text().strip() for o in q.locator("label").all() if o.inner_text().strip()], "type": _detect_type(q)}
        for i, q in enumerate(q_locs)
    ]
    return q_locs, questions
