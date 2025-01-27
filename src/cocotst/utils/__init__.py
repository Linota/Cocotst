from typing import Optional

from cocotst.message.element import Ark, Element, Embed, Markdown, MediaElement


def get_msg_type(content: str = "", element: Optional[Element] = None):
    if isinstance(element, MediaElement):
        return 7
    if isinstance(element, Markdown):
        return 2
    if isinstance(element, Ark):
        return 3
    if isinstance(element, Embed):
        return 4
    if content:
        return 0
