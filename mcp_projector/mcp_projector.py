#!/usr/bin/env python3
"""
MCP Projector Server - A minimal FastMCP server template

This server demonstrates a basic MCP server using HTTP transport
that responds with "hello world" functionality.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from fastmcp import FastMCP

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

# Configuration variables from environment
project_folders_root = os.getenv("PROJECT_FOLDERS_ROOT")
projects_json_file_path = os.getenv("PROJECTS_JSON_FILE_PATH")
# Filter strategy: "AND" or "OR" (default: "AND")
filter_strategy = os.getenv("FILTER_STRATEGY", "AND").upper()

# Create the FastMCP server instance
mcp = FastMCP("Projector")

def load_and_filter_projects(filter_keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Load projects from JSON file and filter by keywords using configurable strategy.
    
    Args:
        filter_keywords: List of keywords to filter by (case-insensitive)
        
    Returns:
        List of projects that match the filter keywords based on the configured strategy
        - AND strategy: project must match ALL filter keywords
        - OR strategy: project must match ANY filter keyword
    """
    try:
        with open(projects_json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        projects = data.get('projects', [])
        
        if not filter_keywords:
            return projects
        
        # Convert filter keywords to lowercase for case-insensitive matching
        filter_keywords_lower = [kw.lower() for kw in filter_keywords]
        
        filtered_projects = []
        for project in projects:
            # Check if any keyword in the project matches any filter keyword
            project_keywords = [kw.lower() for kw in project.get('keywords', [])]
            
            # Also check in title for broader matching
            title_words = project.get('title', '').lower().split()
            all_searchable_terms = project_keywords + title_words
            
            if filter_strategy == "AND":
                # AND strategy: project must match ALL filter keywords
                matches_all = True
                for filter_kw in filter_keywords_lower:
                    if not any(filter_kw in term for term in all_searchable_terms):
                        matches_all = False
                        break
                if matches_all:
                    filtered_projects.append(project)
            else:
                # OR strategy: if any filter keyword matches any project term
                if any(filter_kw in term for filter_kw in filter_keywords_lower 
                       for term in all_searchable_terms):
                    filtered_projects.append(project)
        
        return filtered_projects
        
    except FileNotFoundError:
        print(f"Warning: Projects file not found at {projects_json_file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing projects JSON: {e}")
        return []
    except Exception as e:
        print(f"Error loading projects: {e}")
        return []

@mcp.tool
def find_projects(keywords: list[str]) -> str:
    """Find projects based on a list of keywords using configurable strategy.
    
    Args:
        keywords: List of keywords to search for (case-insensitive)
        
    Returns:
        JSON string containing matching projects with only their IDs and titles
        
    Note:
        The filtering strategy is configurable via FILTER_STRATEGY environment variable:
        - "AND": project must match ALL keywords (default)
        - "OR": project must match ANY keyword
    """
    filtered_projects = load_and_filter_projects(keywords)
    
    # Filter results to contain only ID and title, removing keywords
    filtered_results = []
    for project in filtered_projects:
        filtered_results.append({
            "id": project.get("id"),
            "title": project.get("title")
        })
    
    # Format the results for better readability
    if not filtered_results:
        strategy_text = "all" if filter_strategy == "AND" else "any"
        return json.dumps({
            "message": f"No projects found matching {strategy_text} keywords: {', '.join(keywords)} (using {filter_strategy} strategy)",
            "projects": []
        }, indent=2)
    
    strategy_text = "all" if filter_strategy == "AND" else "any"
    result = {
        "message": f"Found {len(filtered_results)} projects matching {strategy_text} keywords: {', '.join(keywords)} (using {filter_strategy} strategy)",
        "projects": filtered_results
    }
    
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.resource("projector://status")
def get_status():
    """Get the current status of the projector server."""
    return {
        "status": "running",
        "message": "MCP Projector Server is operational",
        "version": "1.0.0"
    }

@mcp.prompt
def welcome_prompt() -> str:
    """Generate a welcome prompt for the projector server."""
    return "Welcome to the MCP Projector Server! Available tools: find_projects (search projects by keywords), create_new_project_folder (create date-based project folders), and create_readme_in_folder (generate README.md files with templates)."

def create_project_folder() -> Dict[str, Any]:
    """
    Create a new project folder in PROJECT_FOLDERS_ROOT with naming scheme pYYYYMMDDa.
    
    Returns:
        Dict containing status, message, and folder_path information
    """
    if not project_folders_root:
        return {
            "status": "error",
            "message": "PROJECT_FOLDERS_ROOT environment variable not set",
            "folder_path": None
        }
    
    if not os.path.exists(project_folders_root):
        return {
            "status": "error", 
            "message": f"PROJECT_FOLDERS_ROOT directory does not exist: {project_folders_root}",
            "folder_path": None
        }
    
    # Generate folder name with current date in pYYYYMMDDa format
    current_date = datetime.now()
    folder_name = f"p{current_date.strftime('%Y%m%d')}a"
    folder_path = os.path.join(project_folders_root, folder_name)
    
    # Check if folder already exists
    if os.path.exists(folder_path):
        return {
            "status": "exists",
            "message": f"Folder already exists: {folder_name}",
            "folder_path": folder_path
        }
    
    # Create the folder
    try:
        os.makedirs(folder_path)
        return {
            "status": "created",
            "message": f"Successfully created folder: {folder_name}",
            "folder_path": folder_path
        }
    except OSError as e:
        return {
            "status": "error",
            "message": f"Failed to create folder {folder_name}: {str(e)}",
            "folder_path": None
        }

@mcp.tool
def create_new_project_folder() -> str:
    """Create a new project folder with current date in the PROJECT_FOLDERS_ROOT directory.
    
    The folder will be named using the format pYYYYMMDDa (e.g., p20250621a for June 21, 2025).
    If the folder already exists, it will not be created again.
    
    Returns:
        JSON string containing the operation status, message, and folder path
    """
    result = create_project_folder()
    return json.dumps(result, indent=2, ensure_ascii=False)

def create_readme_file(folder_path: str, title: str, keywords: List[str]) -> Dict[str, Any]:
    """
    Create a README.md file in the specified folder with a template.
    
    Args:
        folder_path: Path to the folder where README.md should be created
        title: Title for the README
        keywords: List of keywords to include in the template
        
    Returns:
        Dict containing status, message, and file_path information
    """
    if not folder_path:
        return {
            "status": "error",
            "message": "Folder path is required",
            "file_path": None
        }
    
    if not os.path.exists(folder_path):
        return {
            "status": "error",
            "message": f"Folder does not exist: {folder_path}",
            "file_path": None
        }
    
    if not os.path.isdir(folder_path):
        return {
            "status": "error",
            "message": f"Path is not a directory: {folder_path}",
            "file_path": None
        }
    
    readme_path = os.path.join(folder_path, "README.md")
    
    # Check if README.md already exists
    if os.path.exists(readme_path):
        return {
            "status": "exists",
            "message": f"README.md already exists in {folder_path}",
            "file_path": readme_path
        }
    
    # Format keywords with # prefix
    formatted_keywords = " ".join(f"#{kw}" for kw in keywords) if keywords else ""
    
    # Create README content with template
    readme_content = f"""# {title}

> **Keywords**: {formatted_keywords}

"""
    
    # Write README.md file
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return {
            "status": "created",
            "message": f"Successfully created README.md in {folder_path}",
            "file_path": readme_path
        }
    except OSError as e:
        return {
            "status": "error",
            "message": f"Failed to create README.md: {str(e)}",
            "file_path": None
        }

@mcp.tool
def create_readme_in_folder(folder_path: str, title: str, keywords: list[str] = None) -> str:
    """Create a README.md file in the specified folder with a template.
    
    Args:
        folder_path: Path to the folder where README.md should be created
        title: Title for the README
        keywords: Optional list of keywords to include (will be prefixed with #)
        
    Returns:
        JSON string containing the operation status, message, and file path
    """
    if keywords is None:
        keywords = []
    
    result = create_readme_file(folder_path, title, keywords)
    return json.dumps(result, indent=2, ensure_ascii=False)

def main():
    """Run the MCP server with SSE transport."""
    print("Starting MCP Projector Server...")
    print("Server will be available at: http://127.0.0.1:8000/sse")
    
    # Run with SSE transport (Server-Sent Events) for Langflow compatibility
    mcp.run(
        transport="sse",
        host="127.0.0.1",
        port=8000
    )

if __name__ == "__main__":
    main()
