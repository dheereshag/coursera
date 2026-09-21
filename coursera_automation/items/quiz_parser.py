"""DOM extraction and question classification for Coursera quizzes."""

from playwright.sync_api import Locator


def _detect_type(q_loc: Locator) -> str:
    """Classify question as single or multiselect."""
    return "multiselect" if q_loc.locator('input[type="checkbox"], [role="checkbox"]').count() else "single"


def _extract_prompt(q_loc: Locator) -> str:
    """Extract question prompt from cml-viewer or container."""
    c = q_loc.locator('[data-testid="cml-viewer"]:not(label *)').first
    c = (
        c
        if c.is_visible(timeout=100)
        else q_loc.locator('xpath=preceding::div[@data-testid="cml-viewer"][not(ancestor::label)][1]').first
    )
    return str(c.inner_text().strip()) if c.is_visible(timeout=200) else str(q_loc.inner_text().strip())
