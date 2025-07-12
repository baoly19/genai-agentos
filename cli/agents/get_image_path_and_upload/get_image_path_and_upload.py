import asyncio, base64, httpx, json
from typing import Annotated
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext

AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNTk0NTMzNi1hYmNlLTQ5ODItOGY3OC1lOTk1ZDdjZTg3YWYiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjM0ZDAyNjI2LWVhNTAtNDhkMi04NWM1LWNkODUzNzViZjdlZSJ9.6fB9hbfFtYqB3Rh-nISYuK6krmvr8z_A3Wn4bMtJfVw" # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

MCP_ENDPOINT = "https://8a0988f0ce7f.ngrok-free.app"  # note the /mcp path
# ----------------------------------------------------------------------------

session = GenAISession(jwt_token=AGENT_JWT)

@session.bind(
    name="get_image_path_and_upload",
    description="Read a file from context and upload it to the MedVLM MCP server, returning an upload:// URI"
)
async def get_image_path_and_upload(
    agent_context: GenAIContext,
    file_id: Annotated[str, "ID of the file to upload"]
) -> str:
    """
    1. Fetch the file bytes from the GenAI Files API.
    2. Send those bytes to the FastMCP `upload_image` tool.
    3. Return the resulting `upload://<uuid>` URI.
    """
    # 1. grab bytes from GenAI file storage
    file_obj = await agent_context.files.get_by_id(file_id)
    file_bytes: bytes = file_obj.read()

    # 2. b64-encode for transport
    b64_payload = base64.b64encode(file_bytes).decode()

    # 3. JSON-RPC request payload
    rpc_call = {
        "jsonrpc": "2.0",
        "id": 1,                              # any unique ID is fine
        "method": "tools/call",
        "params": {
            "tool": "upload_image",
            "arguments": {"b64": b64_payload}
        }
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(MCP_ENDPOINT, json=rpc_call)
        resp.raise_for_status()

    # 4. FastMCP returns {"result": {"output": "upload://<uuid>"}} (or just the string)
    data = resp.json()
    result = data.get("result", {})
    # normalise for either shape
    upload_uri = result.get("output") if isinstance(result, dict) else result
    if not upload_uri:
        raise RuntimeError(f"Unexpected MCP response: {json.dumps(data, indent=2)}")

    return upload_uri



async def main():
    print(f"Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
