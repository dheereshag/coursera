"""Option matching and selection for Coursera quiz choices."""

import re
from typing import Any

from playwright.sync_api import Locator


def normalize_opt(s: Any) -> str:
    """Normalize whitespace, punctuation, and math symbols for robust comparison."""
    return re.sub(r"[\s\*\u00d7\.,;:\(\)\$\\\{\}]+", " ", str(s).lower()).strip()


def resolve_option_index(opt: Any, options: list[str], max_count: int) -> int | None:
    """Resolve target option index via integer, letter (A-D), or normalized text."""
    if isinstance(opt, int) and 0 <= opt < max_count:
        return opt
    if isinstance(opt, str) and len(s := opt.strip().upper()) == 1 and s in "ABCD":
        return "ABCD".index(s)
    if n_opt := normalize_opt(opt):
        for i, o in enumerate(options):
            n_o = normalize_opt(o)
            if n_opt == n_o or n_opt in n_o or n_o in n_opt:
                return i
    return None


def click_option(q_loc: Locator, opt: Any, options: list[str]) -> None:
    """Click or check option label on question locator using index or text filter."""
    labels = q_loc.locator("label")
    idx = resolve_option_index(opt, options, labels.count())
    btn = labels.nth(idx) if idx is not None and idx < labels.count() else labels.filter(has_text=str(opt)).first
    if btn.is_visible():
        if btn.locator('input[type="checkbox"]').count():
            btn.locator('input[type="checkbox"]').first.check(force=True)
        else:
            btn.click(force=True)
