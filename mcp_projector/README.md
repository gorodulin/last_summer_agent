# MCP Projector Server

A minimal MCP server template using FastMCP with HTTP transport for project search and filtering.

## Features

- **SSE Transport**: Uses Server-Sent Events (SSE) for Langflow compatibility
- **Project Search**: Find projects by keywords with configurable AND/OR filtering
- **Status Resource**: Provides server status information
- **Welcome Prompt**: Template prompt for user interaction
- **Configurable Filtering**: Support for both AND and OR logic when filtering projects

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using uv:
```bash
uv pip install fastmcp
```

## Configuration

The server uses environment variables for configuration:

- `PROJECT_FOLDERS_ROOT`: Root directory for project folders
- `PROJECTS_JSON_FILE_PATH`: Path to the JSON file containing project data
- `FILTER_STRATEGY`: Filtering strategy for keywords ("AND" or "OR", default: "AND")
  - "AND": Projects must match ALL provided keywords
  - "OR": Projects must match ANY of the provided keywords

Create a `.env` file with your configuration:
```bash
PROJECT_FOLDERS_ROOT=/path/to/your/projects
PROJECTS_JSON_FILE_PATH=/path/to/your/projects.json
FILTER_STRATEGY=AND
```

## Usage

### Running the Server

```bash
python mcp_projector.py
```

The server will start on `http://127.0.0.1:8000/sse`

### Available Tools

1. **find_projects(keywords)** - Find projects by keywords using configurable AND/OR filtering
   - Takes a list of keywords (case-insensitive)
   - Returns projects matching the keywords based on the configured strategy
   - Searches both project keywords and title words

2. **create_new_project_folder()** - Create a new project folder with current date
   - Creates a folder named using the format `pYYYYMMDDa` (e.g., `p20250621a`)
   - Uses the current date automatically
   - Creates the folder in the `PROJECT_FOLDERS_ROOT` directory
   - Will not create the folder if it already exists

3. **create_readme_in_folder(folder_path, title, keywords)** - Create a README.md file with template
   - Creates a README.md file in the specified folder
   - Uses a predefined template with title and keywords
   - Keywords are automatically prefixed with # (e.g., #python #web)
   - Will not overwrite existing README.md files

## README Template Example

When using the `create_readme_in_folder` tool with title "My Project" and keywords ["python", "web", "api"], the generated README.md will look like:

```markdown
# My Project

> **Keywords**: #python #web #api

```

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
        # Test find_projects tool with AND strategy
        result = await client.call_tool("find_projects", {"keywords": ["python", "web"]})
        print(f"Projects Result: {result.text}")
        
        # Test create_new_project_folder tool
        result = await client.call_tool("create_new_project_folder", {})
        print(f"Create Folder Result: {result.text}")
        
        # Test create_readme_in_folder tool
        result = await client.call_tool("create_readme_in_folder", {
            "folder_path": "/path/to/project/folder",
            "title": "My Project",
            "keywords": ["python", "web", "api"]
        })
        print(f"Create README Result: {result.text}")
        
        # Test status resource
        resource = await client.read_resource("projector://status")
        print(f"Status: {resource.content}")

if __name__ == "__main__":
    asyncio.run(test_server())
```

## Filter Strategy Examples

### AND Strategy (default)
```bash
FILTER_STRATEGY=AND
```
When searching for keywords `["python", "web"]`, only projects that contain BOTH "python" AND "web" in their keywords or title will be returned.

### OR Strategy
```bash
FILTER_STRATEGY=OR
```
When searching for keywords `["python", "web"]`, projects that contain EITHER "python" OR "web" (or both) in their keywords or title will be returned.

## Transport Options

The server is configured to use HTTP transport, but you can easily switch to other transports:

- **STDIO** (default): `mcp.run()`
- **SSE**: `mcp.run(transport="sse", host="127.0.0.1", port=8000)`
- **Streamable HTTP**: `mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")`
