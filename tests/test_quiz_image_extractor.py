"""Tests for quiz question image extractor."""

from unittest.mock import MagicMock

from coursera_automation.items.quiz.image_extractor import extract_question_images


def test_extract_question_images_from_cml_viewer() -> None:
    """Verify images extracted from visible cml-viewer locator."""
    mock_q = MagicMock()
    mock_c = MagicMock()
    mock_c.is_visible.return_value = True

    img1, img2, img_dup = MagicMock(), MagicMock(), MagicMock()
    img1.get_attribute.return_value = "https://example.com/diagram1.png"
    img2.get_attribute.return_value = "//example.com/diagram2.png"
    img_dup.get_attribute.return_value = "https://example.com/diagram1.png"

    mock_c.locator.return_value.all.return_value = [img1, img2, img_dup]
    mock_q.locator.return_value.first = mock_c

    urls = extract_question_images(mock_q)
    assert urls == [
        "https://example.com/diagram1.png",
        "https://example.com/diagram2.png",
    ]


def test_extract_question_images_fallback_when_cml_viewer_hidden() -> None:
    """Verify fallback locator used when primary prompt viewer is hidden."""
    mock_q = MagicMock()
    mock_c = MagicMock()
    mock_c.is_visible.return_value = False

    fallback_img = MagicMock()
    fallback_img.get_attribute.return_value = "https://example.com/fallback.png"

    mock_q.locator.return_value.first = mock_c
    mock_q.locator.return_value.all.return_value = [fallback_img]

    urls = extract_question_images(mock_q)
    assert urls == ["https://example.com/fallback.png"]


def test_extract_question_images_filters_invalid_urls() -> None:
    """Verify non-http/data URLs are discarded."""
    mock_q = MagicMock()
    mock_c = MagicMock()
    mock_c.is_visible.return_value = True

    img_invalid, img_valid = MagicMock(), MagicMock()
    img_invalid.get_attribute.return_value = "javascript:void(0)"
    img_valid.get_attribute.return_value = "data:image/png;base64,iVBORw0KGgoAAAANS..."

    mock_c.locator.return_value.all.return_value = [img_invalid, img_valid]
    mock_q.locator.return_value.first = mock_c

    urls = extract_question_images(mock_q)
    assert urls == ["data:image/png;base64,iVBORw0KGgoAAAANS..."]


def test_extract_question_images_empty() -> None:
    """Verify empty list returned when no images are found."""
    mock_q = MagicMock()
    mock_c = MagicMock()
    mock_c.is_visible.return_value = True
    mock_c.locator.return_value.all.return_value = []
    mock_q.locator.return_value.first = mock_c
    mock_q.locator.return_value.all.return_value = []

    assert extract_question_images(mock_q) == []
