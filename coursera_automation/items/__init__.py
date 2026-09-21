"""Item-level automation handlers organized into domain subpackages."""

from coursera_automation.items.dispatcher import dispatch_item, process_items

__all__ = ["dispatch_item", "process_items"]
