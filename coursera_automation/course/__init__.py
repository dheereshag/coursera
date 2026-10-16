"""Course navigation subpackage."""

from coursera_automation.course.cta import wait_for_cta
from coursera_automation.course.open import open_course

__all__ = ["open_course", "wait_for_cta"]
