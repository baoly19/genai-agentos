import asyncio
from typing import Annotated
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
import base64
from fastmcp import Client

AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyNmIwY2U5My0wN2I0LTRmYmItOTIxNC04ZDIyMTdkMDNiNzQiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjM0ZDAyNjI2LWVhNTAtNDhkMi04NWM1LWNkODUzNzViZjdlZSJ9.YaVRK9TyL7oF-5dz1AU8Lr0NoeSOgi1rvzqIgBxWv1M" # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

MCP_URL = "https://896e41804afd.ngrok-free.app/mcp"
@session.bind(
    name="get_image_and_upload_mcp",
    description="Get image and upload to ai mcp server"
)
async def get_image_and_upload_mcp(
    agent_context: GenAIContext,
    file_id: Annotated[str, "ID of the image file to upload"]
):
    # 1. Get the file content
    file = await agent_context.files.get_by_id(file_id)
    file_bytes = file.read()

    # 2. Convert to base64
    b64_img = base64.b64encode(file_bytes).decode("utf-8")

    async with Client(MCP_URL) as client:
        # 2. Upload the image
        upload_result = await client.call_tool("upload_image", {"b64": b64_img})
        print("✅ Uploaded:", upload_result.data)

        return {
            "status": "uploaded",
            "image_uri": upload_result.data
        }



async def main():
    print(f"Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
