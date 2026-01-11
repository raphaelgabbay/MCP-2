import os
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

WORKDIR = "./mcp-workspace"
MODEL_ID = "gemini-2.5-flash"

SYSTEM_PROMPT = f"""
You are an agent running locally on Windows.

You have MCP tools for:
- filesystem access LIMITED to: {WORKDIR}
- git operations for repo at: ./

Rules:
- Never write outside {WORKDIR}.
- Prefer listing directories before reading files.
- Use tools when helpful; do not hallucinate file contents.
"""

async def main():
    # if not os.getenv("GOOGLE_API_KEY"):
    #     raise RuntimeError("GOOGLE_API_KEY not set in environment")

    mcp_connections = {
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", WORKDIR],
        },
        "git": {
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "mcp_server_git", "--repository", WORKDIR],
        },
    }

    client = MultiServerMCPClient(mcp_connections, tool_name_prefix=True)
    tools = await client.get_tools()
    # print("TOOLS: ", tools)

    llm = ChatGoogleGenerativeAI(model=MODEL_ID, temperature=0.2, api_key=os.getenv("GOOGLE_API_KEY"))
    agent = create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)

    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "List files, read README.md, add a short project plan section, then commit changes."
        }]
    })

    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())