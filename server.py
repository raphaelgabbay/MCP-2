from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DemoServer")

@mcp.tool()
def add(a: int, b: int) -> int:
    'Add two integers.'
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    'Multiply two integers.'
    return a * b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    'Return a greeting string.'
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()