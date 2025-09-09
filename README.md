# MCP Bitbucket Review Server

This is an MCP server for LLMs to use capabilities of bitbucket to it's code review workflows.

## Installation

> [!IMPORTANT]  
> You need python 3.10 or above for this to work.

Install from pip:

```bash
pip install mcp-bitbucket-review
```

## Configuration in Cursor

1.  Go to `File` -> `Preferences` -> `Cursor Settings` -> `MCP & Integrations`.

2.  Add a new MCP server.

3.  Add the bitbucket server MCP from the following to the mcpServers object of mcp.json:
    ```jsonc
    {
        "mcpServers": {
            // ... your rest of the MCP servers
            "bitbucket": {
                "command": "mcp-bitbucket-review-server",
                "env": {
                    "BITBUCKET_EMAIL": "YOUR_BITBUCKET_EMAIL",
                    "BITBUCKET_API_TOKEN": "YOUR_BITBUCKET_API_TOKEN"
                }
            }
        }
    }

4.  Save the settings.

## Usage sample

Open new chat and give following prompt:

> Review pull request <YOUR_PULL_REQUEST_URL>


## Get API token from bitbucket

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens

2. Click on button labelled `Create API token with scopes`

3. Give scopes and store the API token. Make sure you give the following scopes to the API token:
    ```
    read:pullrequest:bitbucket
    write:pullrequest:bitbucket
    read:repository:bitbucket
    ```

Happy coding!
