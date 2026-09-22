"""DOM extraction and question classification for Coursera quizzes."""

from contextlib import suppress
from typing import Any

from playwright.sync_api import Error, Locator, Page

Q_SEL = 'fieldset, [role="radiogroup"], [role="group"], .rc-Option, [id^="prompt-autoGradableResponseId"], textarea'


def _is_textarea(loc: Locator) -> bool:
    with suppress(Error, AttributeError):
        return loc.evaluate("el => el.tagName") == "TEXTAREA"
    return False


def _find_textarea(loc: Locator) -> Locator:
    if _is_textarea(loc) or loc.locator("textarea").count():
        return loc if _is_textarea(loc) else loc.locator("textarea").first
    with suppress(Error, AttributeError):
        if isinstance(p := loc.get_attribute("id"), str) and p and (t := loc.page.locator(f'textarea[aria-labelledby="{p}"]').first).is_visible(timeout=100):
            return t
    return loc.locator("xpath=following::textarea[1]").first


def _detect_type(q_loc: Locator) -> str:
    with suppress(Error, AttributeError):
        if isinstance(p := q_loc.get_attribute("id"), str) and p and q_loc.page.locator(f'textarea[aria-labelledby="{p}"]').count():
            return "textarea"
    if _is_textarea(q_loc) or q_loc.locator("textarea").count():
        return "textarea"
    return "multiselect" if q_loc.locator('input[type="checkbox"], [role="checkbox"]').count() else "single"


def _extract_prompt(q_loc: Locator) -> str:
    c = q_loc.locator('[data-testid="cml-viewer"]:not(label *)').first
    if not c.is_visible(timeout=100) and (lid := q_loc.get_attribute("aria-labelledby")):
        c = q_loc.page.locator(f'[id="{lid}"]').first
    c = c if c.is_visible(timeout=100) else q_loc.locator('xpath=preceding::div[@data-testid="cml-viewer"][not(ancestor::label)][1]').first
    return str(c.inner_text().strip()) if c.is_visible(timeout=100) else str(q_loc.get_attribute("placeholder") or q_loc.inner_text().strip())


def _find_question_locs(page: Page) -> list[Locator]:
    locs = [q for q in page.locator('fieldset, [role="radiogroup"], [role="group"], div:has(> * > .rc-Option), textarea:not(fieldset textarea)').all() if not q.locator("#agreement-checkbox-base").count()]
    return locs or [q for q in page.locator('[id^="prompt-autoGradableResponseId"], [data-testid*="question"]').all() if not q.locator("#agreement-checkbox-base").count()]


def wait_and_extract_questions(page: Page, timeout_ms: int) -> tuple[list[Locator], list[dict[str, Any]]]:
    with suppress(Error):
        page.locator(Q_SEL).first.wait_for(state="attached", timeout=timeout_ms)
    q_locs: list[Locator] = []
    for _ in range(10):
        if (q_locs := _find_question_locs(page)) and any(q.locator("label, input, textarea").all() or _is_textarea(q) for q in q_locs):
            break
        page.wait_for_timeout(1000)
    questions = [
        {"index": i, "question": _extract_prompt(q), "options": [o.inner_text().strip() for o in q.locator("label").all() if o.inner_text().strip()], "type": _detect_type(q)}
        for i, q in enumerate(q_locs)
    ]
    return q_locs, questions
