from typing import Any, Optional
import json
import os
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import requests

load_dotenv()

mcp = FastMCP("rag_tool")

@mcp.tool()
def matlab_troubleshooter_tool(user_query: str, image_path: Optional[str] = None) -> str:
    """
    A tool to troubleshoot MATLAB code using a RAG agent.
    Sends the query and optionally an image to a FastAPI endpoint and formats the response.

    Args:
        user_query (str): User's MATLAB-related query or error message to troubleshoot.
        image_path (Optional[str]): Path to the screenshot/image to upload.

    Returns:
        str: JSON string containing the final response, reference links, and relevant documents.
    """
    import requests

    url = "https://800d-2409-40d7-e8-dce-4026-1aab-2ef2-879d.ngrok-free.app/process"

    try:
        files = {"query": (None, user_query)}

        if image_path and os.path.isfile(image_path):
            files["image"] = (os.path.basename(image_path), open(image_path, "rb"), "image/png")

        response = requests.post(url, files=files)
        response.raise_for_status()

        response_data = response.json()

        return json.dumps(response_data, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")

# print(matlab_troubleshooter_tool("Error: Cannot connect to target 'TargetPC1': Cannot connect to target. in Matlab"))