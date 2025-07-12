import asyncio
from datetime import datetime

from genai_session.session import GenAISession

session = GenAISession(
    jwt_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3MzgyNGQxMi03OWJmLTQ5NWMtYTAzZC0zZDcwNzZhMjA1NzQiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjY5NjVlNWMwLTE0MzQtNDkzNS1hYTAwLWFjZTIxNTVmMTE5YSJ9.CHNjiQELtfPPMki_lu3CDCRe_4ct7GA_NBMaFSypWHk"
)


@session.bind(name="get_current_date", description="Return current date")
async def get_current_date(agent_context):
    agent_context.logger.info("Inside get_current_date")
    return datetime.now().strftime("%Y-%m-%d")


async def main():
    await session.process_events()


if __name__ == "__main__":
    asyncio.run(main())
