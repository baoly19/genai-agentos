import asyncio
from typing import Annotated
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import Optional, Literal
from typing import Annotated, Literal, Optional
from pubmedclient.models import Db, EFetchRequest, ESearchRequest
from pubmedclient.sdk import efetch, esearch, pubmedclient_client
from genai_session.session import GenAISession, GenAIContext
from pydantic import BaseModel, Field
import os
from openai import OpenAI

load_dotenv()

AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwYTdlZGNlMi0wYjFhLTQwMTMtOGY0ZC05Y2Q4OTU5MGI4MjciLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjhhNTM3MjVmLTMzNzAtNDk3ZS05MDU5LWQ1MmRmOTdmZjE0OSJ9._UEJgf0RKP2NUPXYHwnEDUqy9ZYJ-OwoW2yl3PRG3Q4" # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

EMAIL = os.getenv("PUBMED_EMAIL")  # must be set
API_KEY = os.getenv("PUBMED_API_KEY")  # optional, but recommended

#Modify mcp for request
class SearchAbstractsRequest(BaseModel):
    term: str = Field(..., description="Text query to search in PubMed.")
    retmax: Optional[int] = 20
    sort: Optional[str] = None
    field: Optional[str] = None
    datetype: Optional[Literal["mdat", "pdat", "edat"]] = None
    reldate: Optional[int] = None
    mindate: Optional[str] = None
    maxdate: Optional[str] = None


# 3. Bind tool to GenAI session
@session.bind(
    name="search_pubmed_abstracts",
    description="Search abstracts in PubMed and return a list of articles"
)
async def search_abstracts_handler(
    agent_context: GenAIContext,
    request: Annotated[SearchAbstractsRequest, "Parameters to search PubMed abstracts"]
) -> Annotated[str, "Search results as free-text summary"]:
    email = os.getenv("PUBMED_EMAIL")

    async with pubmedclient_client() as client:
        # Search
        search_model = SearchAbstractsRequest(**request) if isinstance(request, dict) else request
        search_req = ESearchRequest(db=Db.PUBMED, **search_model.model_dump())
        search_resp = await esearch(client, search_req)

        ids = search_resp.esearchresult.idlist
        if not ids:
            return "❌ No articles found."

        # Fetch (use 'abstract' or 'xml')
        fetch_req = EFetchRequest(
            db=Db.PUBMED,
            id=",".join(ids[:search_model.retmax]),  # Only first result
            retmode="text",
            rettype="abstract"
        )
        fetch_resp = await efetch(client, fetch_req)

        # OpenAI GPT summary
        system_prompt = "You are a medical assistant summarizing research articles."
        user_prompt = (
            "Please summarize the key findings and conclusions from the following articles:\n\n"
            f"{fetch_resp}"
        )

        client = OpenAI(api_key=os.getenv("OPENAPI_KEY"), base_url = "https://api.braintrust.dev/v1/proxy")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=512,
        )

        summary = completion.choices[0].message.content.strip()
        return summary

async def main():
    print(f"Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
