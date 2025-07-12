import asyncio
from typing import Annotated
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
# from generate_prescription_pdf import generate_treatment_pdf

load_dotenv()

OPENAPI_KEY = os.environ.get("OPENAPI_KEY")

AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NjhiMzM5NC01MWVkLTQzN2EtOTk0NC1lNmQyYjg1YzllZjEiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjY5NjVlNWMwLTE0MzQtNDkzNS1hYTAwLWFjZTIxNTVmMTE5YSJ9.zZjlKO13QfV-V9myGmr1Hu0X1kCEH7bw4wmRFIK_dVM" # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

openai_client = OpenAI(api_key=OPENAPI_KEY, base_url="https://api.braintrust.dev/v1/proxy")

@session.bind(
    name="treatment_recommender",
    description=(
        "Generate a treatment plan for the most likely diagnosis, including medication, "
        "dosage, lifestyle suggestions, and medical cautions."
    )
)
async def treatment_recommender(
    agent_context: GenAIContext,
    diagnosis_data: Annotated[str, "Output from Diagnosis Reasoning Agent"]
):
    """
    Use the most likely diagnosis to generate a treatment plan:
    - recommended drug(s)
    - dosage and duration
    - lifestyle suggestions
    - medical cautions
    """
    agent_context.logger.info("Running Treatment Recommendation Agent")

    prompt = f"""
You are a clinical treatment assistant.

The patient has been most likely diagnosed with:
{diagnosis_data}

Generate a treatment plan including:
- 1–2 medications (name, dosage, duration)
- 2 lifestyle recommendations
- 1–2 medical cautions

Return only the result in this JSON format:
{{
  "condition": "diagnosed condition name",
  "medications": [
    {{
      "name": "drug name",
      "dosage": "dosage and frequency",
      "duration": "duration of treatment"
    }}
  ],
  "lifestyle": [
    "lifestyle suggestion 1",
    "lifestyle suggestion 2"
  ],
  "cautions": [
    "caution 1",
    "caution 2"
  ]
}}
"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    result = response.choices[0].message.content.strip()
    agent_context.logger.info(f"Treatment plan result: {result}")
    # pdf_path = generate_treatment_pdf(result, patient_id="anonymous-001")

    return {"treatment_plan": result}


async def main():
    print(f"Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
