#!/usr/bin/env python3

import json
import os
import subprocess
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
    return "Welcome to the MCP Projector Server! Available tools: find_projects (search projects by keywords), create_project_and_open (complete project setup), and project_details (fetch README content from project folders)."

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

def create_project_with_readme(title: str, keywords: List[str]) -> Dict[str, Any]:
    """
    Create a new project folder with README and open it in Finder.
    
    This function combines:
    1. Creating a new project folder with a README.md file with the provided title and keywords
    2. Opening the folder in macOS Finder (non-blocking)
    
    Args:
        title: Title for the project and README
        keywords: List of keywords for the README
        
    Returns:
        Dict containing status, message, folder_path, and readme_path information
    """
    if not title:
        return {
            "status": "error",
            "message": "Title is required",
            "folder_path": None,
            "readme_path": None
        }
    
    # Step 1: Create project folder
    folder_result = create_project_folder()
    
    if folder_result["status"] == "error":
        return {
            "status": "error",
            "message": f"Failed to create project folder: {folder_result['message']}",
            "folder_path": None,
            "readme_path": None
        }
    
    folder_path = folder_result["folder_path"]
    
    # Step 2: Create README.md in the new folder
    readme_result = create_readme_file(folder_path, title, keywords)
    
    if readme_result["status"] == "error":
        return {
            "status": "partial",
            "message": f"Project folder created but README failed: {readme_result['message']}",
            "folder_path": folder_path,
            "readme_path": None
        }
    
    # Step 3: Open folder in macOS Finder (non-blocking)
    try:
        subprocess.Popen(["open", folder_path])
        open_status = "opened"
        open_message = "and opened in Finder"
    except Exception as e:
        open_status = "not_opened"
        open_message = f"but failed to open in Finder: {str(e)}"
    
    # Determine overall status
    if folder_result["status"] == "exists":
        if readme_result["status"] == "exists":
            status = "all_exist"
            message = f"Project folder and README already exist {open_message}"
        else:
            status = "folder_exists_readme_created"
            message = f"Project folder already existed, README created {open_message}"
    else:
        if readme_result["status"] == "exists":
            status = "folder_created_readme_exists"
            message = f"Project folder created, README already existed {open_message}"
        else:
            status = "all_created"
            message = f"Project folder and README created successfully {open_message}"
    
    return {
        "status": status,
        "message": message,
        "folder_path": folder_path,
        "readme_path": readme_result["file_path"],
        "open_status": open_status
    }

@mcp.tool
def create_project_and_open(title: str, keywords: list[str] = None) -> str:
    """Create a new project folder with README and open it in macOS Finder.
    
    This tool creates a new project
    
    Args:
        title: Title for the project and README
        keywords: Optional list of keywords for the README (will be prefixed with #)
        
    Returns:
        JSON string containing the operation status, messages, and file paths
    """
    if keywords is None:
        keywords = []
    
    result = create_project_with_readme(title, keywords)
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

def get_project_readme(project_id: str) -> Dict[str, Any]:
    """
    Fetch README.md content from a project folder by project ID.
    
    Args:
        project_id: The ID of the project folder to read from
        
    Returns:
        Dict containing status, message, project_id, and readme_content
    """
    if not project_id:
        return {
            "status": "error",
            "message": "Project ID is required",
            "project_id": None,
            "readme_content": None
        }
    
    if not project_folders_root:
        return {
            "status": "error",
            "message": "PROJECT_FOLDERS_ROOT environment variable not set",
            "project_id": project_id,
            "readme_content": None
        }
    
    if not os.path.exists(project_folders_root):
        return {
            "status": "error",
            "message": f"PROJECT_FOLDERS_ROOT directory does not exist: {project_folders_root}",
            "project_id": project_id,
            "readme_content": None
        }
    
    # Construct project folder path
    project_folder_path = os.path.join(project_folders_root, project_id)
    
    # Check if project folder exists
    if not os.path.exists(project_folder_path):
        return {
            "status": "not_found",
            "message": f"Project folder not found: {project_id}",
            "project_id": project_id,
            "readme_content": None
        }
    
    if not os.path.isdir(project_folder_path):
        return {
            "status": "error",
            "message": f"Project path is not a directory: {project_id}",
            "project_id": project_id,
            "readme_content": None
        }
    
    # Construct README.md path
    readme_path = os.path.join(project_folder_path, "README.md")
    
    # Check if README.md exists
    if not os.path.exists(readme_path):
        return {
            "status": "no_readme",
            "message": f"README.md not found in project: {project_id}",
            "project_id": project_id,
            "readme_content": None
        }
    
    # Try to read README.md content
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        return {
            "status": "success",
            "message": f"Successfully read README.md from project: {project_id}",
            "project_id": project_id,
            "readme_content": readme_content
        }
    except Exception as e:
        return {
            "status": "read_error",
            "message": f"Failed to read README.md from project {project_id}: {str(e)}",
            "project_id": project_id,
            "readme_content": None
        }

@mcp.tool
def project_details(project_id: str) -> str:
    """Fetch README.md content from a project folder by project ID.
    
    This tool searches for a project folder in PROJECT_FOLDERS_ROOT and reads
    its README.md file. It handles missing folders and files gracefully.
    
    Args:
        project_id: The ID/name of the project folder to read from
        
    Returns:
        JSON string containing the operation status, message, project_id, and README content
    """
    result = get_project_readme(project_id)
    return json.dumps(result, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
