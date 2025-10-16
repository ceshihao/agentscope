# -*- coding: utf-8 -*-
"""The tool response class."""

from dataclasses import dataclass, field
from typing import Optional, List

from .._utils._common import _get_timestamp
from ..message import AudioBlock, ImageBlock, TextBlock


@dataclass
class ToolResponse:
    """The result chunk of a tool call."""

    content: List[TextBlock | ImageBlock | AudioBlock]
    """The execution output of the tool function."""

    metadata: Optional[dict] = None
    """The metadata to be accessed within the agent, so that we don't need to
    parse the tool result block."""

    stream: bool = False
    """Whether the tool output is streamed."""

    is_last: bool = True
    """Whether this is the last response in a stream tool execution."""

    is_interrupted: bool = False
    """Whether the tool execution is interrupted."""

    id: str = field(default_factory=lambda: _get_timestamp(True))
    """The identity of the tool response."""


@dataclass
class ToolConfirmationResponse(ToolResponse):
    """Special ToolResponse for tools that require user confirmation."""
    
    tool_name: str = ""
    """The name of the tool that requires confirmation."""
    
    tool_args: dict = None
    """The arguments for the tool that requires confirmation."""
    
    confirmation_message: str = ""
    """The message to show to the user for confirmation."""
    
    def __init__(
        self,
        tool_name: str,
        tool_args: dict,
        confirmation_message: str,
    ) -> None:
        if tool_args is None:
            tool_args = {}
        super().__init__(
            content=[
                TextBlock(
                    type="text",
                    text=f"<tool-confirmation-required>"
                    f"Tool: {tool_name}\n"
                    f"Args: {tool_args}\n"
                    f"Message: {confirmation_message}"
                    f"</tool-confirmation-required>",
                ),
            ],
            metadata={
                "tool_confirmation_required": True,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "confirmation_message": confirmation_message,
            },
        )
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.confirmation_message = confirmation_message
