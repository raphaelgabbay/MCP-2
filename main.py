from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="mcp",  # Executable
    args=["run", "server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available resources
            resources = await session.list_resources()
            print("📜 LISTING RESOURCES")
            for resource in resources:
                print("Resource: ", resource)

            # List available tools (and peek at schemas)
            tools = await session.list_tools()
            print("⚒️ LISTING TOOLS")
            functions = []
            for tool in tools.tools:
                print("Tool: ", tool.name)
                print("Tool", tool.inputSchema["properties"])    
                functions.append(convert_to_llm_tool(tool))
            
            print(" Functions")
            print(functions)

            prompt = "Multiply 2 by 20"
            
            # ask LLM what tools to all, if any
            functions_to_call = call_llm(prompt, functions)
            
            # call suggested functions
            for f in functions_to_call:
                result = await session.call_tool(f["name"], arguments=f["args"])
                print("TOOLS result: ", result.content)
            

def convert_to_llm_tool(tool):
    tool_schema = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "type": "function",
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema["properties"]
            }
        }
    }

    return tool_schema

# llm
from cerebras.cloud.sdk import Cerebras
import json
from dotenv import load_dotenv
import os


# llm
def call_llm(prompt, functions):

    # Load environment variables from the .env file (if present)
    load_dotenv()

    token = os.getenv("CEREBRAS_TOKEN")

    model_name = "llama-3.3-70b"

    client = Cerebras(api_key=token)

    print("CALLING LLM")
    response = client.chat.completions.create(
        messages=[
            {
            "role": "system",
            "content": "You are a helpful assistant.",
            },
            {
            "role": "user",
            "content": prompt,
            },
        ],
        model=model_name,
        tools = functions,
        # Optional parameters
        temperature=1.,
        max_tokens=1000,
        top_p=1.    
    )

    response_message = response.choices[0].message

    functions_to_call = []

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            print("TOOL: ", tool_call)
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            functions_to_call.append({ "name": name, "args": args })

    return functions_to_call

if __name__ == "__main__":
    import asyncio

    asyncio.run(run())