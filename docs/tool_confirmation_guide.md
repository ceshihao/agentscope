# 工具确认功能使用说明

## 概述

AgentScope 现在支持在工具执行前进行用户确认的功能。这个功能允许用户为每个工具设置是否需要二次确认，在用户确认后执行工具，在用户拒绝后不执行工具。

## 功能特性

- **灵活配置**: 可以为每个工具单独设置是否需要确认
- **多种确认方式**: 支持终端确认和 Studio 确认
- **MCP 工具支持**: 完全支持 MCP 工具的确认功能
- **用户友好**: 提供清晰的中文提示和交互界面

## 使用方法

### 1. 基本工具确认

```python
from agentscope.tool import (
    Toolkit,
    TerminalToolConfirmation,
    set_confirmation_handler,
    ToolResponse,
)
from agentscope.message import TextBlock

# 创建工具包
toolkit = Toolkit()

# 设置确认处理器
confirmation_handler = TerminalToolConfirmation("确认执行工具")
set_confirmation_handler(confirmation_handler)

# 定义工具函数
async def dangerous_operation():
    return ToolResponse(
        content=[TextBlock(type="text", text="危险操作已执行！")],
    )

# 注册需要确认的工具
toolkit.register_tool_function(
    tool_func=dangerous_operation,
    group_name="basic",
    func_description="危险操作，需要用户确认",
    need_confirmation=True,  # 设置为 True 表示需要确认
)
```

### 2. MCP 工具确认

```python
from agentscope.mcp import StdIOStatefulClient

# 创建 MCP 客户端
mcp_client = StdIOStatefulClient(
    name="example_mcp",
    command=["python", "-m", "example_mcp_server"],
)

# 连接到 MCP 服务器
await mcp_client.connect()

# 注册 MCP 工具，指定某些工具需要确认
await toolkit.register_mcp_client(
    mcp_client=mcp_client,
    group_name="basic",
    need_confirmation_funcs=["dangerous_operation", "file_delete"],  # 这些工具需要确认
)
```

### 3. 自定义确认处理器

```python
from agentscope.tool import ToolConfirmationBase

class CustomConfirmation(ToolConfirmationBase):
    async def request_confirmation(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        **kwargs: Any,
    ) -> bool:
        # 自定义确认逻辑
        print(f"自定义确认: {tool_name}")
        print(f"参数: {tool_args}")
        
        # 这里可以实现任何确认逻辑
        # 例如：发送邮件、调用 API、记录日志等
        
        response = input("是否执行? (y/n): ").strip().lower()
        return response in ['y', 'yes', '是', '确认']

# 设置自定义确认处理器
set_confirmation_handler(CustomConfirmation())
```

## 确认处理器类型

### TerminalToolConfirmation

终端确认处理器，通过命令行与用户交互：

```python
from agentscope.tool import TerminalToolConfirmation

# 使用默认提示
handler = TerminalToolConfirmation()

# 自定义提示
handler = TerminalToolConfirmation("请确认是否执行此操作")
```

### StudioToolConfirmation

Studio 确认处理器，通过 AgentScope Studio 界面与用户交互：

```python
from agentscope.tool import StudioToolConfirmation

# 使用默认 Studio URL
handler = StudioToolConfirmation()

# 自定义 Studio URL
handler = StudioToolConfirmation("http://localhost:3000")
```

## 工作流程

1. **工具注册**: 在注册工具时设置 `need_confirmation=True`
2. **工具调用**: 当 Agent 尝试调用需要确认的工具时
3. **确认请求**: 系统会调用确认处理器请求用户确认
4. **用户响应**: 用户可以选择确认或拒绝
5. **执行结果**: 
   - 如果用户确认：正常执行工具
   - 如果用户拒绝：返回拒绝消息，不执行工具

## 示例场景

### 场景 1: 文件操作确认

```python
async def delete_file(file_path: str):
    """删除文件操作，需要确认"""
    import os
    os.remove(file_path)
    return ToolResponse(
        content=[TextBlock(type="text", text=f"文件 {file_path} 已删除")],
    )

toolkit.register_tool_function(
    tool_func=delete_file,
    group_name="basic",
    func_description="删除指定文件",
    need_confirmation=True,
)
```

### 场景 2: 系统命令确认

```python
async def execute_system_command(command: str):
    """执行系统命令，需要确认"""
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return ToolResponse(
        content=[TextBlock(type="text", text=f"命令执行结果: {result.stdout}")],
    )

toolkit.register_tool_function(
    tool_func=execute_system_command,
    group_name="basic",
    func_description="执行系统命令",
    need_confirmation=True,
)
```

### 场景 3: 网络请求确认

```python
async def send_http_request(url: str, method: str = "GET"):
    """发送 HTTP 请求，需要确认"""
    import requests
    response = requests.request(method, url)
    return ToolResponse(
        content=[TextBlock(type="text", text=f"响应状态: {response.status_code}")],
    )

toolkit.register_tool_function(
    tool_func=send_http_request,
    group_name="basic",
    func_description="发送 HTTP 请求",
    need_confirmation=True,
)
```

## 注意事项

1. **确认处理器**: 必须在使用前设置确认处理器
2. **异步支持**: 所有确认操作都是异步的
3. **错误处理**: 如果用户拒绝，工具不会执行，会返回相应的拒绝消息
4. **MCP 工具**: MCP 工具的确认功能通过 `need_confirmation_funcs` 参数控制
5. **默认行为**: 如果没有设置确认处理器，会默认使用 `TerminalToolConfirmation`

## 扩展功能

可以通过继承 `ToolConfirmationBase` 类来实现自定义的确认逻辑，例如：

- 集成到现有的用户界面系统
- 添加日志记录功能
- 实现批量确认
- 添加确认超时机制
- 集成到权限管理系统

这个功能为 AgentScope 提供了更安全和可控的工具执行环境，特别适用于生产环境中的敏感操作。
