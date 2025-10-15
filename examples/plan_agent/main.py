import asyncio
import os

from agentscope.agent import ReActAgent, UserAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.model import DashScopeChatModel
from agentscope.mcp import HttpStatelessClient
from agentscope.plan import PlanNotebook
from agentscope.tool import Toolkit, TerminalToolConfirmation, set_confirmation_handler


async def main() -> None:
  """通过 MCP 连接 localhost:8000/mcp 的 ReActAgent，支持阿里云运维工具。

  其中 `OOS_RebootInstances` 工具启用终端二次确认。
  """

  # 1) 工具与二次确认
  toolkit = Toolkit()
  set_confirmation_handler(TerminalToolConfirmation("请确认是否执行该工具"))

  # 2) 连接 MCP（streamable_http）到本地服务 http://localhost:8000/mcp
  mcp_client = HttpStatelessClient(
    name="alibaba_cloud_ops_mcp",
    transport="streamable_http",
    url="http://localhost:8000/mcp",
  )

  # 仅对敏感操作启用二次确认：OOS_RebootInstances
  await toolkit.register_mcp_client(
    mcp_client=mcp_client,
    # group_name="alibaba_cloud_ops",
    need_confirmation_funcs=["OOS_RebootInstances"],
  )

  # 3) 构建 ReActAgent（保留 PlanNotebook）
  agent = ReActAgent(
    name="Alibaba Cloud Ops Assistant",
    sys_prompt="你是一个有用的助手，具备阿里云资源运维能力。",
    model=DashScopeChatModel(
      model_name="qwen-max-latest",
      api_key=os.environ["DASHSCOPE_API_KEY"],
    ),
    formatter=DashScopeChatFormatter(),
    plan_notebook=PlanNotebook(),
    toolkit=toolkit,
  )

  # 4) 用户交互循环：复杂任务将自动进入计划模式
  user = UserAgent(name="user")
  msg = None
  while True:
    msg = await user(msg)
    if msg.get_text_content() == "exit":
      break
    msg = await agent(msg)


asyncio.run(main())