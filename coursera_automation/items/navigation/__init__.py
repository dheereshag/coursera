"""Navigation controls and dialog handlers for Coursera automation."""

from coursera_automation.items.navigation.dialogs import (
    dismiss_dialogs,
    register_dialog_handlers,
)
from coursera_automation.items.navigation.navigator import click_next_item, click_resume

__all__ = ["click_next_item", "click_resume", "dismiss_dialogs", "register_dialog_handlers"]
