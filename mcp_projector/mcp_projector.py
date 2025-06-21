#!/usr/bin/env python3
"""
MCP Projector Server - A minimal FastMCP server template

This server demonstrates a basic MCP server using HTTP transport
that responds with "hello world" functionality.
"""

import json
import os
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
    return "Welcome to the MCP Projector Server! You can use the find_projects tool to search for projects by keywords."

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
