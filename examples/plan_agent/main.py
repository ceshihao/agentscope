import asyncio
import os

from agentscope.agent import ReActAgent, UserAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.model import DashScopeChatModel
from agentscope.mcp import HttpStatelessClient
from agentscope.plan import PlanNotebook
from agentscope.pipeline import stream_printing_messages
from agentscope.tool import Toolkit, UserAgentToolConfirmation
from agentscope.message import Msg
import agentscope

agentscope.init(
    # ...
    studio_url="http://localhost:3000"
)


async def main() -> None:
  """ReActAgent connected to localhost:8000/mcp via MCP, supporting Alibaba Cloud operations.

  Tools with names containing Describe/Get/Query are read-only and don't require confirmation,
  while other tools require user confirmation before execution.
  """

  # 1) Toolkit and confirmation setup
  toolkit = Toolkit()
  toolkit.set_confirmation_handler(UserAgentToolConfirmation("Confirm tool execution"))

  # 2) Connect MCP (streamable_http) to local service http://localhost:8000/mcp
  mcp_client = HttpStatelessClient(
    name="alibaba_cloud_ops_mcp",
    transport="streamable_http",
    url="http://localhost:8000/mcp",
  )

  # Dynamic confirmation setup: tools with Describe/Get/Query in name are read-only (no confirmation), others require confirmation
  all_tools = await mcp_client.list_tools()
  readonly_keywords = ["describe", "get", "query"]
  need_confirmation_funcs = []
  for t in all_tools:
    name_lower = t.name.lower()
    if not any(kw in name_lower for kw in readonly_keywords):
      need_confirmation_funcs.append(t.name)

  await toolkit.register_mcp_client(
    mcp_client=mcp_client,
    need_confirmation_funcs=need_confirmation_funcs,
  )

  # 3) Build ReActAgent (keeping PlanNotebook)
  agent = ReActAgent(
    name="Alibaba Cloud Ops Assistant",
    sys_prompt="You are a helpful assistant with Alibaba Cloud operations capabilities.如果用户输入的不明确或不足以制定计划，请反问用户提供更多相关信息。",
    model=DashScopeChatModel(
      model_name="qwen-max-latest",
      api_key=os.environ["DASHSCOPE_API_KEY"],
    ),
    formatter=DashScopeChatFormatter(),
    plan_notebook=PlanNotebook(
      max_subtasks=5,
    ),
    toolkit=toolkit,
  )

  # Set agent reference in toolkit for confirmation message generation
  toolkit.set_agent(agent)

  # 4) User interaction loop: complex tasks will automatically enter plan mode
  user = UserAgent(name="user")
  msg_list = []
  plan_first = Msg(
        "system",
        (
          "Before executing any tools or taking any actions, you must first call 'create_plan' "
          "to create a complete plan with clear goals, steps, and expected outcomes, "
          "then proceed with subsequent operations. 如果用户输入的不明确或不足以制定计划，请反问用户提供更多相关信息。"
        ),
        "system",
      )
  msg_list.append(plan_first)
  while True:      
    msg = await user(msg_list)
    msg_list.append(msg)
    
    if msg.get_text_content() == "exit":
      break

    # Always use full message history for processing
    reply_msg = await agent(msg_list)
    msg_list.append(reply_msg)
    # We disable the terminal printing to avoid messy outputs
    # agent.set_console_output_enabled(False)

    # obtain the printing messages from the agent in a streaming way
    # async for msg, last in stream_printing_messages(
    #     agents=[agent],
    #     coroutine_task=agent(msg),
    # ):
    #     print(msg, last)


asyncio.run(main())