# -*- coding: utf-8 -*-
"""Tool confirmation mechanism for AgentScope."""

from abc import abstractmethod
from typing import Any


class ToolConfirmationBase:
    """Base class for tool confirmation mechanisms."""

    @abstractmethod
    async def request_confirmation(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        **kwargs: Any,
    ) -> bool:
        """Request user confirmation for tool execution.

        Args:
            tool_name (`str`):
                The name of the tool to be executed.
            tool_args (`dict[str, Any]`):
                The arguments that will be passed to the tool.
            **kwargs:
                Additional keyword arguments.

        Returns:
            `bool`:
                `True` if the user confirms the execution, `False` otherwise.
        """
        pass


class TerminalToolConfirmation(ToolConfirmationBase):
    """Terminal-based tool confirmation."""

    def __init__(self, confirmation_prompt: str = "确认执行工具") -> None:
        """Initialize the terminal confirmation handler.

        Args:
            confirmation_prompt (`str`, defaults to `"确认执行工具"`):
                The prompt text to display when requesting confirmation.
        """
        self.confirmation_prompt = confirmation_prompt

    async def request_confirmation(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        **kwargs: Any,
    ) -> bool:
        """Request user confirmation via terminal input.

        Args:
            tool_name (`str`):
                The name of the tool to be executed.
            tool_args (`dict[str, Any]`):
                The arguments that will be passed to the tool.
            **kwargs:
                Additional keyword arguments.

        Returns:
            `bool`:
                `True` if the user confirms the execution, `False` otherwise.
        """
        print(f"\n{self.confirmation_prompt}: {tool_name}")
        print(f"参数: {tool_args}")
        
        while True:
            response = input("是否执行? (y/n): ").strip().lower()
            if response in ['y', 'yes', '是', '确认']:
                return True
            elif response in ['n', 'no', '否', '取消']:
                return False
            else:
                print("请输入 y/yes/是/确认 或 n/no/否/取消")


class StudioToolConfirmation(ToolConfirmationBase):
    """Studio-based tool confirmation."""

    def __init__(self, studio_url: str = "http://localhost:3000") -> None:
        """Initialize the studio confirmation handler.

        Args:
            studio_url (`str`, defaults to `"http://localhost:3000"`):
                The URL of the AgentScope Studio.
        """
        self.studio_url = studio_url

    async def request_confirmation(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        **kwargs: Any,
    ) -> bool:
        """Request user confirmation via Studio interface.

        Args:
            tool_name (`str`):
                The name of the tool to be executed.
            tool_args (`dict[str, Any]`):
                The arguments that will be passed to the tool.
            **kwargs:
                Additional keyword arguments.

        Returns:
            `bool`:
                `True` if the user confirms the execution, `False` otherwise.
        """
        # This would integrate with the Studio interface
        # For now, we'll use a simple implementation
        print(f"\nStudio确认: {tool_name}")
        print(f"参数: {tool_args}")
        
        while True:
            response = input("是否执行? (y/n): ").strip().lower()
            if response in ['y', 'yes', '是', '确认']:
                return True
            elif response in ['n', 'no', '否', '取消']:
                return False
            else:
                print("请输入 y/yes/是/确认 或 n/no/否/取消")


# Global confirmation handler instance
_confirmation_handler: ToolConfirmationBase | None = None


def set_confirmation_handler(handler: ToolConfirmationBase) -> None:
    """Set the global tool confirmation handler.

    Args:
        handler (`ToolConfirmationBase`):
            The confirmation handler to use.
    """
    global _confirmation_handler
    _confirmation_handler = handler


def get_confirmation_handler() -> ToolConfirmationBase:
    """Get the current tool confirmation handler.

    Returns:
        `ToolConfirmationBase`:
            The current confirmation handler.

    Raises:
        `RuntimeError`:
            If no confirmation handler has been set.
    """
    global _confirmation_handler
    if _confirmation_handler is None:
        # Default to terminal confirmation
        _confirmation_handler = TerminalToolConfirmation()
    return _confirmation_handler


async def request_tool_confirmation(
    tool_name: str,
    tool_args: dict[str, Any],
    **kwargs: Any,
) -> bool:
    """Request confirmation for tool execution using the global handler.

    Args:
        tool_name (`str`):
            The name of the tool to be executed.
        tool_args (`dict[str, Any]`):
            The arguments that will be passed to the tool.
        **kwargs:
            Additional keyword arguments.

    Returns:
        `bool`:
            `True` if the user confirms the execution, `False` otherwise.
    """
    handler = get_confirmation_handler()
    return await handler.request_confirmation(tool_name, tool_args, **kwargs)
