# MCP Projector Server

A minimal MCP server template using FastMCP with HTTP transport.

## Features

- **SSE Transport**: Uses Server-Sent Events (SSE) for Langflow compatibility
- **Hello World Tool**: Simple tool that returns "Hello World" message
- **Greet Tool**: Personalized greeting tool
- **Status Resource**: Provides server status information
- **Welcome Prompt**: Template prompt for user interaction

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using uv:
```bash
uv pip install fastmcp
```

## Usage

### Running the Server

```bash
python mcp_projector.py
```

The server will start on `http://127.0.0.1:8000/sse`

### Available Tools

1. **hello_world()** - Returns a simple "Hello World" message
2. **greet(name)** - Greets someone by name (defaults to "World")

### Available Resources

1. **projector://status** - Returns server status and version information

### Available Prompts

1. **welcome_prompt()** - Generates a welcome message for users

## Testing

You can test the server using the FastMCP client:

```python
from fastmcp import Client
import asyncio

async def test_server():
    async with Client("http://127.0.0.1:8000/sse") as client:
        # Test hello_world tool
        result = await client.call_tool("hello_world", {})
        print(f"Hello World Result: {result.text}")
        
        # Test greet tool
        result = await client.call_tool("greet", {"name": "Alice"})
        print(f"Greet Result: {result.text}")
        
        # Test status resource
        resource = await client.read_resource("projector://status")
        print(f"Status: {resource.content}")

if __name__ == "__main__":
    asyncio.run(test_server())
```

## Transport Options

The server is configured to use HTTP transport, but you can easily switch to other transports:

- **STDIO** (default): `mcp.run()`
- **SSE**: `mcp.run(transport="sse", host="127.0.0.1", port=8000)`
- **Streamable HTTP**: `mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")`
