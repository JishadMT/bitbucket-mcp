import os
from typing import Optional, Dict, Any
from datetime import datetime
import re
import base64
from urllib.parse import urlparse
import requests
from fastmcp import FastMCP

mcp = FastMCP("Bitbucket MCP Server")

@mcp.tool
def get_bitbucket_creds() -> tuple:
    """Retrieve Bitbucket credentials from environment variables.
    Returns:
        tuple: Containing the Bitbucket email and API token.
    """
    api_token = os.getenv('BITBUCKET_API_TOKEN')
    email = os.getenv('BITBUCKET_EMAIL')

    if not api_token or not email:
        raise ValueError("Missing Bitbucket credentials")

    return email, api_token

@mcp.tool
def parse_bitbucket_pr_url(pr_url: str) -> tuple:
    """
    Parse a Bitbucket pull request URL to extract workspace, repository, and PR ID.
    
    Args:
        pr_url (str): Bitbucket pull request URL
    
    Returns:
        tuple: (workspace, repo_slug, pr_id) as strings
        
    Raises:
        ValueError: If the URL is not a valid Bitbucket PR URL
    """
    if not pr_url or not isinstance(pr_url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Clean up the URL
    pr_url = pr_url.strip()
    if not pr_url.startswith(('http://', 'https://')):
        pr_url = 'https://' + pr_url
    
    parsed = urlparse(pr_url)
    
    # Bitbucket Cloud PR patterns
    cloud_patterns = [
        r'/([^/]+)/([^/]+)/pull-requests/(\d+)',
        r'/([^/]+)/([^/]+)/pull-requests/(\d+)/[^/]*'
    ]
    
    # Bitbucket Server/Data Center PR patterns  
    server_patterns = [
        r'/projects/([^/]+)/repos/([^/]+)/pull-requests/(\d+)',
        r'/projects/([^/]+)/repos/([^/]+)/pull-requests/(\d+)/[^/]*'
    ]
    
    workspace = None
    repo_slug = None
    pr_id = None
    
    # Check Bitbucket Cloud (bitbucket.org)
    if 'bitbucket.org' in parsed.netloc.lower():
        for pattern in cloud_patterns:
            match = re.search(pattern, parsed.path)
            if match:
                workspace = match.group(1)
                repo_slug = match.group(2) 
                pr_id = match.group(3)
                break
    
    # Check Bitbucket Server/Data Center
    else:
        for pattern in server_patterns:
            match = re.search(pattern, parsed.path)
            if match:
                workspace = match.group(1)  # Project key for server
                repo_slug = match.group(2)
                pr_id = match.group(3)
                break
    
    if not workspace or not repo_slug or not pr_id:
        raise ValueError(f"Invalid Bitbucket PR URL format: {pr_url}")
    
    return workspace, repo_slug, pr_id

@mcp.tool
def get_pr_details(
    workspace: str,
    repo_slug: str,
    pr_id: int,
    email: str,
    api_token: str
) -> Dict[str, Any]:
    """
    Get detailed information about a Bitbucket pull request.
    
    Args:
        workspace (str): Bitbucket workspace name
        repo_slug (str): Repository name/slug
        pr_id (int): Pull request ID
        email (str): Atlassian account email
        api_token (str): Bitbucket API token (App password)
    
    Returns:
        Dict[str, Any]: Detailed pull request information
        
    Raises:
        requests.RequestException: If the API request fails
        ValueError: If the pull request is not found
    """
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}"
    
    # Create base64 encoded credentials
    credentials = f"{email}:{api_token}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Accept': '*/*',
        'User-Agent': 'Python-Bitbucket-Client/1.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        pr_data = response.json()
        
        # Extract and format key information
        details = {
            'id': pr_data['id'],
            'title': pr_data['title'],
            'description': pr_data.get('description', ''),
            'state': pr_data['state'],
            'created_on': pr_data['created_on'],
            'updated_on': pr_data['updated_on'],
            'author': {
                'display_name': pr_data['author']['display_name'],
                'username': pr_data['author']['nickname'],
                'uuid': pr_data['author']['uuid']
            },
            'source_branch': pr_data['source']['branch']['name'],
            'destination_branch': pr_data['destination']['branch']['name'],
            'source_commit': pr_data['source']['commit']['hash'],
            'destination_commit': pr_data['destination']['commit']['hash'],
            'reviewers': [
                {
                    'display_name': reviewer['display_name'],
                    'username': reviewer['nickname'],
                    'approved': reviewer.get('approved', False)
                }
                for reviewer in pr_data.get('reviewers', [])
            ],
            'participants': [
                {
                    'display_name': participant['user']['display_name'],
                    'username': participant['user']['nickname'],
                    'role': participant['role'],
                    'approved': participant.get('approved', False)
                }
                for participant in pr_data.get('participants', [])
            ],
            'comment_count': pr_data.get('comment_count', 0),
            'task_count': pr_data.get('task_count', 0),
            'close_source_branch': pr_data.get('close_source_branch', False),
            'merge_commit': pr_data.get('merge_commit', {}).get('hash') if pr_data.get('merge_commit') else None,
            'links': pr_data['links']
        }
        
        return details
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch PR details: {e} Basic {encoded_credentials.decode()}")

@mcp.tool
def get_bitbucket_pr_diff(
    workspace: str,
    repo_slug: str,
    pr_id: int,
    email: str,
    api_token: str,
    context_lines: Optional[int] = 3,
    ignore_whitespace: bool = True,
    binary: bool = False
) -> str:
    """
    Get the diff for a Bitbucket pull request.
    
    Args:
        workspace (str): Bitbucket workspace name
        repo_slug (str): Repository name/slug
        pr_id (int): Pull request ID
        email (str): Atlassian account email
        api_token (str): Bitbucket API token (App password)
        context_lines (int, optional): Number of context lines around changes. Defaults to 3.
        ignore_whitespace (bool): Whether to ignore whitespace changes. Defaults to True.
        binary (bool): Whether to include binary file diffs. Defaults to False.
    
    Returns:
        str: The diff content as a string
        
    Raises:
        requests.RequestException: If the API request fails
    """
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/diff"
    
    # Create base64 encoded credentials
    credentials = f"{email}:{api_token}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Accept': 'text/plain',
        'User-Agent': 'Python-Bitbucket-Client/1.0'
    }
    
    # Build query parameters
    params = {}
    if context_lines is not None:
        params['context'] = context_lines
    if ignore_whitespace:
        params['ignore_whitespace'] = 'true'
    if binary:
        params['binary'] = 'true'
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.text
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch PR diff: {e}")

def main():
    mcp.run()

if __name__ == "__main__":
    main()