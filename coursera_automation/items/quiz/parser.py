"""DOM extraction and question classification for Coursera quizzes."""

from contextlib import suppress
from typing import Any

from playwright.sync_api import Error, Locator, Page

from .image_extractor import extract_question_images
from .loader import load_and_stabilize_questions

TEXT_SEL = 'textarea:not([aria-hidden="true"]):not([readonly]), input:not([type="radio"]):not([type="checkbox"]):not([type="hidden"]):not([readonly]), [contenteditable="true"], [data-slate-editor="true"]'


def _is_textarea(loc: Locator) -> bool:
    with suppress(Error, AttributeError):
        tag = loc.evaluate("el => el.tagName")
        return tag == "TEXTAREA" or loc.get_attribute("contenteditable") == "true" or (tag == "INPUT" and str(loc.get_attribute("type") or "text").lower() not in ("radio", "checkbox", "hidden"))
    return False


def _find_textarea(loc: Locator) -> Locator:
    if _is_textarea(loc) or (ta := loc.locator(TEXT_SEL)).count():
        return loc if _is_textarea(loc) else ta.first
    with suppress(Error, AttributeError):
        if isinstance(p := loc.get_attribute("id"), str) and p and (t := loc.page.locator(f'{TEXT_SEL}[aria-labelledby="{p}"]').first).is_visible(timeout=100):
            return t
    return loc.locator(TEXT_SEL).first


def _detect_type(q_loc: Locator) -> str:
    if q_loc.locator('input[type="checkbox"], [role="checkbox"]').count():
        return "multiselect"
    with suppress(Error, AttributeError):
        if isinstance(p := q_loc.get_attribute("id"), str) and p and q_loc.page.locator(f'{TEXT_SEL}[aria-labelledby="{p}"]').count():
            return "textarea"
    return "textarea" if _is_textarea(q_loc) or q_loc.locator(TEXT_SEL).count() else "single"


def _extract_prompt(q_loc: Locator) -> str:
    c = q_loc.locator('[id^="prompt-"] [data-testid="cml-viewer"], [data-testid="legend"] [data-testid="cml-viewer"], [data-testid="cml-viewer"]:not(label *)').first
    if not c.is_visible(timeout=100) and (lid := q_loc.get_attribute("aria-labelledby")):
        c = q_loc.page.locator(f'[id="{lid}"]').first
    c = c if c.is_visible(timeout=100) else q_loc.locator('xpath=preceding::div[@data-testid="cml-viewer"][not(ancestor::label)][1]').first
    txt = str(c.inner_text().strip()) if c.is_visible(timeout=100) else str(q_loc.get_attribute("placeholder") or q_loc.inner_text().strip())
    return txt.split("You are a helpful AI assistant")[0].strip()


def _find_question_locs(page: Page) -> list[Locator]:
    parts = [q for q in page.locator('[data-testid^="part-Submission_"]').all() if not q.locator("#agreement-checkbox-base").count()]
    if parts:
        return parts
    locs = [q for q in page.locator(f'[data-testid^="part-"]:has({TEXT_SEL}, .rc-Option), fieldset:not([aria-hidden="true"]), [role="radiogroup"]').all() if not q.locator("#agreement-checkbox-base").count()]
    return locs or [q for q in page.locator(f'[id^="prompt-autoGradableResponseId"], {TEXT_SEL}').all() if not q.locator("#agreement-checkbox-base").count()]


def wait_and_extract_questions(page: Page, timeout_ms: int) -> tuple[list[Locator], list[dict[str, Any]]]:
    q_locs = load_and_stabilize_questions(page, timeout_ms, _find_question_locs)
    questions = [{"index": i, "question": _extract_prompt(q), "images": extract_question_images(q), "options": [o.inner_text().strip() for o in q.locator("label").all() if o.inner_text().strip()], "type": _detect_type(q)} for i, q in enumerate(q_locs)]
    return q_locs, questions
