"""Extract image URLs from Coursera quiz question DOM elements."""

from contextlib import suppress

from playwright.sync_api import Error, Locator


def extract_question_images(q_loc: Locator) -> list[str]:
    """Extract and deduplicate image URLs associated with a question prompt."""
    c = q_loc.locator(
        '[id^="prompt-"] [data-testid="cml-viewer"], [data-testid="legend"] [data-testid="cml-viewer"], [data-testid="cml-viewer"]:not(label *)'
    ).first
    imgs = c.locator("img").all() if c.is_visible(timeout=100) else []
    if not imgs:
        imgs = q_loc.locator('[id^="prompt-"] img, [data-testid="legend"] img, figure img:not(label *)').all()
    urls: list[str] = []
    for img in imgs:
        with suppress(Error, AttributeError):
            if src := (img.get_attribute("src") or "").strip():
                clean = f"https:{src}" if src.startswith("//") else src
                if clean.startswith(("http://", "https://", "data:image/")) and clean not in urls:
                    urls.append(clean)
    return urls
