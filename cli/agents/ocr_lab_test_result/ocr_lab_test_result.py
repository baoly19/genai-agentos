import asyncio
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any, List
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
# OCR deps (sync, but we’ll off-load them to a thread pool)
from pdf2image import convert_from_bytes          # pip install pdf2image
import pytesseract                                # pip install pytesseract
from PIL import Image 
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5Mjk2MzhjNy1lMGE2LTQyNGQtOWVjNS1mYmJmYzEzMjY0NzIiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjM0ZDAyNjI2LWVhNTAtNDhkMi04NWM1LWNkODUzNzViZjdlZSJ9.0LNmjs84uX-iK3hF9eyz5y3bkkUfj7nPy_9sx09XRII" # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

def _pdf_bytes_to_text(pdf_bytes: bytes, *, dpi: int = 300, lang: str = "eng") -> str:
    """Blocking helper: convert PDF bytes → text via pytesseract."""
    pages = convert_from_bytes(pdf_bytes, dpi=dpi)  # list[PIL.Image]
    chunks: list[str] = []

    for idx, img in enumerate(pages, start=1):
        txt = pytesseract.image_to_string(img, lang=lang).strip()
        chunks.append(f"\n\n===== Page {idx} =====\n{txt}")

    return "\n".join(chunks)




@session.bind(
    name="ocr_lab_test_result",
    description="agent to extract information from lab report pdf"
)
async def ocr_lab_test_result(
    agent_context,
    file_id: Annotated[str, "ID of the PDF to OCR"],
    lang: Annotated[str, "Tesseract language(s), e.g. 'eng' or 'eng+vie'"] = "eng",
    dpi:  Annotated[int,  "Rasterisation DPI (quality vs speed)"]          = 300,
):
# ▶ 1. fetch
    file = await agent_context.files.get_by_id(file_id)
    pdf_bytes = file.read()

    # ▶ 2. OCR (runs in default ThreadPoolExecutor so we don’t block the event loop)
    loop = asyncio.get_running_loop()
    text: str = await loop.run_in_executor(
        None, _pdf_bytes_to_text, pdf_bytes
    )
    # Use openai to summarize the text
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url = "https://braintrust.dev/proxy/v1")

    response = client.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a helpful assistant. Summarize the findings, and provide a concise summary highlighting the key abnormalities and their potential significance from the lab test result."},
                  {"role": "user", "content": text}],
    )
    summary = response.choices[0].message.content

    if summary:
        return {
            "summary": summary,
        }
    else:
        return {
            "summary": "No summary found",
        }


async def main():
    print(f"Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
