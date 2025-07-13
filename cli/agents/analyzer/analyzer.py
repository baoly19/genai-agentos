import asyncio
from typing import Annotated
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

OPENAPI_KEY = os.environ.get("OPENAPI_KEY")


AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MDU0NmQ1Ni1jMzRjLTRkOWEtYmM4YS1hNTg3NmQ2ZjJhNTAiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjhhNTM3MjVmLTMzNzAtNDk3ZS05MDU5LWQ1MmRmOTdmZjE0OSJ9.hUoO1BZ2pTOZPw0F_UbPR-VVkhVW836zX1BaglHx4jo" # noqa: E501

openai_client = OpenAI(api_key=OPENAPI_KEY, base_url="https://api.braintrust.dev/v1/proxy")
session = GenAISession(jwt_token=AGENT_JWT)


@session.bind(
    name="analyzer",
    description="Extract structured triage information from the patient's free-text input. This includes age, gender, relevant medical history, current symptoms, duration, severity, and an overall triage level."
)

async def analyzer(
    agent_context: GenAIContext,
    text: Annotated[str, "Patient's free-text symptoms and description"]
):
    """
    Analyze the patient's symptom description and extract structured triage information.
    """

    agent_context.logger.info("Running Symptom Triage Agent")

    prompt = f"""
    You are an AI medical assistant.

    A patient has submitted the following description:
    \"\"\"
    {text}
    \"\"\"

    Your task is to extract useful information that will assist in triage and future diagnosis.

    Return only a JSON object in the following format:
    {{
    "age": "patient's age if stated or inferred (e.g. 'unknown', 'about 30')",
    "gender": "male | female | unknown",
    "medical_history": [list of relevant past conditions or 'unknown'],
    "symptoms": [list of current symptoms],
    "duration": "duration of symptoms (e.g., '2 days')",
    "severity": "mild | moderate | severe",
    "triage_level": "low | medium | high"
    }}

    Be concise and strictly follow this structure.
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    result = response.choices[0].message.content.strip()
    parsed_result = json.loads(result)  # Parse JSON string to dict
    agent_context.logger.info(f"Triage agent result: {parsed_result}")

    return {"triage_report": parsed_result}


async def main():
    print(f"Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
