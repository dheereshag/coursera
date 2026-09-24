"""Answer filling utilities for quiz questions."""

from contextlib import suppress
from typing import Any

from playwright.sync_api import Error, Locator, Page

from .option_matcher import click_option
from .parser import _find_textarea


def fill_answers(
    page: Page,
    q_locs: list[Locator],
    questions: list[dict[str, Any]],
    answers: dict[int, list[str]],
) -> None:
    """Scroll to and fill textarea or click options for each quiz question."""
    for idx, q_loc in enumerate(q_locs):
        with suppress(Error):
            q_loc.scroll_into_view_if_needed(timeout=1000)
        ans = answers.get(idx, [])
        q_meta = questions[idx] if idx < len(questions) else {}
        if not ans:
            continue
        if q_meta.get("type") == "textarea":
            with suppress(Error):
                (ta := _find_textarea(q_loc)).click()
                ta.fill(ans[0])
        else:
            for opt in ans:
                click_option(q_loc, opt, q_meta.get("options", []))
        page.wait_for_timeout(300)
