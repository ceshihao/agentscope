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
        agent=None,
        **kwargs: Any,
    ) -> bool:
        """Request user confirmation for tool execution.

        Args:
            tool_name (`str`):
                The name of the tool to be executed.
            tool_args (`dict[str, Any]`):
                The arguments that will be passed to the tool.
            agent (optional):
                The agent instance that can be used to generate responses.
            **kwargs:
                Additional keyword arguments.

        Returns:
            `bool`:
                `True` if the user confirms the execution, `False` otherwise.
        """
        pass




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
        # Default to UserAgent confirmation
        _confirmation_handler = UserAgentToolConfirmation()
    return _confirmation_handler


async def request_tool_confirmation(
    tool_name: str,
    tool_args: dict[str, Any],
    agent=None,
    **kwargs: Any,
) -> bool:
    """Request confirmation for tool execution using the global handler.

    Args:
        tool_name (`str`):
            The name of the tool to be executed.
        tool_args (`dict[str, Any]`):
            The arguments that will be passed to the tool.
        agent (optional):
            The agent instance that can be used to generate responses.
        **kwargs:
            Additional keyword arguments.

    Returns:
        `bool`:
            `True` if the user confirms the execution, `False` otherwise.
    """
    handler = get_confirmation_handler()
    return await handler.request_confirmation(tool_name, tool_args, agent, **kwargs)


class UserAgentToolConfirmation(ToolConfirmationBase):
    """Use a UserAgent to request confirmation, unifying terminal/studio input.

    This handler leverages the current `UserAgent` input method (terminal or studio)
    so that the same logic works in both environments.
    """

    def __init__(self, confirmation_prompt: str = "Confirm tool execution") -> None:
        self.confirmation_prompt = confirmation_prompt

    async def request_confirmation(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        agent=None,
        **kwargs: Any,
    ) -> bool:
        # Import here to avoid circular import
        from ..agent import UserAgent
        from ..message import Msg
        
        # If agent is provided, use agent to generate confirmation message
        if agent is not None and hasattr(agent, 'model'):
            # Create a prompt for the agent to generate confirmation message
            confirmation_prompt = (
                f"Please generate a clear confirmation message for the following tool execution:\n"
                f"Tool Name: {tool_name}\n"
                f"Parameters: {tool_args}\n\n"
                f"The message should:\n"
                f"1. Clearly explain what the tool will do\n"
                f"2. Show the parameters in a readable format\n"
                f"3. Ask for user confirmation with clear instructions\n"
                f"4. Use a professional and informative tone"
            )
            
            try:
                # Use agent's model to generate response
                from ..message import Msg
                prompt_msg = Msg("user", confirmation_prompt, "user")
                response_msg = await agent.model.generate([prompt_msg])
                confirmation_msg = response_msg.content
            except Exception as e:
                confirmation_msg = confirmation_prompt
        else:
            # Fallback to static message if no agent provided
            confirmation_msg = (
                f"🔧 **Tool Confirmation Required**\n\n"
                f"**Tool Name:** `{tool_name}`\n"
                f"**Parameters:**\n"
            )
            
            # Format parameters in a readable way
            for key, value in tool_args.items():
                confirmation_msg += f"  - `{key}`: {value}\n"
            
            confirmation_msg += (
                f"\n⚠️ **This tool will be executed. Please confirm:**\n"
                f"- Type `y` or `yes` to **execute** the tool\n"
                f"- Type `n` or `no` to **cancel** the execution"
            )

        # Use UserAgent so it can route to terminal or studio
        user = UserAgent(name="user")
        system_msg = Msg("system", confirmation_msg, "system")
        reply = await user(system_msg)
        text = (reply.get_text_content() or "").strip().lower()
        return text in ["y", "yes"]
