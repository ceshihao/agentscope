import asyncio
import os

from agentscope.agent import ReActAgent, UserAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.model import DashScopeChatModel
from agentscope.mcp import HttpStatelessClient
from agentscope.plan import PlanNotebook
from agentscope.tool import Toolkit, TerminalToolConfirmation, set_confirmation_handler
from agentscope.message import Msg


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

  # 动态设置二次确认：名字包含 Describe/Get/Query 的为只读工具，不需要确认，其他需要确认
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

  # 3) 构建 ReActAgent（保留 PlanNotebook）
  agent = ReActAgent(
    name="Alibaba Cloud Ops Assistant",
    sys_prompt="你是一个有用的助手，具备阿里云资源运维能力。",
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

  # 4) 用户交互循环：复杂任务将自动进入计划模式
  user = UserAgent(name="user")
  msg = None
  while True:
    msg = await user(msg)
    if msg.get_text_content() == "exit":
      break
    if agent.plan_notebook.current_plan is None:
      # 强制先创建计划：在每轮将用户消息交给智能体前，注入 system 提示
      plan_first = Msg(
        "system",
        (
          "在执行任何工具或采取任何行动之前，必须先调用 'create_plan' 创建完整计划，"
          "并在计划明确描述目标、步骤与预期结果后再继续执行后续操作。"
        ),
        "system",
      )
      msg = await agent([plan_first, msg])
    else:
      msg = await agent(msg)


asyncio.run(main())