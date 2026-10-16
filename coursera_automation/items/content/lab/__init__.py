"""Lab content item subpackage."""

from coursera_automation.items.content.lab.agreement import check_lab_agreement
from coursera_automation.items.content.lab.handler import LAUNCH_SEL, handle_lab

_check_agreement = check_lab_agreement

__all__ = ["LAUNCH_SEL", "_check_agreement", "check_lab_agreement", "handle_lab"]
