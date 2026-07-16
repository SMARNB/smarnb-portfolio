import urllib.request
import sys
from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("Blender-Storefront-Bridge")

@mcp.tool()
def execute_blender_script(script: str) -> str:
    """Executes raw Python (bpy) scripts directly in the active Blender session."""
    try:
        # Send the script to the local Blender listener
        req = urllib.request.Request(
            'http://localhost:5000/execute',
            data=script.encode('utf-8'),
            headers={'Content-Type': 'text/plain'}
        )
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"Failed to execute. Is the Blender listener running? Error: {str(e)}"

if __name__ == "__main__":
    # Start the standard input/output server for Claude to talk to
    mcp.run()