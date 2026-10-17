import json
import os
import re
from chunk import chunk_text

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel

from extract import extract_text
from retrieve import score_passages

load_dotenv()


class Answer(BaseModel):
    answer: str
    page: int | None = None


client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"],
    timeout=60,
)


def answer_question(chunks: list[dict], question: str, k: int = 3) -> Answer:
    SYSTEM_PROMPT = """You answer questions about a return policy. Use ONLY the policy excerpts provided and no other information.
                    Reply with ONLY a JSON object like {"answer": "short answer", "page": 2}.
                    "page" is the page number of the excerpt you used.
                    If the answer is not in the excerpts, reply {"answer": "I couldn't find that in the policy.", "page": null}."""
    NOT_FOUND = "I could not find the relevant information, please try again"
    top = score_passages(chunks, question, k)

    if not top:
        return Answer(answer = NOT_FOUND, page = None)

    context = "\n\n".join(f"Page: {p['page']}\n Text: {p['text']}" for p in top)

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Policy exerpts:\n{context}\nQuestion: {question}",
                },
            ],
            temperature=0.2,
            top_p=0.95,
            max_tokens=1500,
            stream=False,
        )
    except OpenAIError:
        return Answer(
            answer="Sorry, the service is unavailable right now. Please try again later.",
            page=None,
    )

    raw = completion.choices[0].message.content or ""

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return Answer(answer=NOT_FOUND, page=None)
    try:
        result = Answer(**json.loads(match.group()))
    except (json.JSONDecodeError, ValueError):
        return Answer(answer=NOT_FOUND, page=None)
    if result.page not in {p["page"] for p in top}:
        result.page = None
    return result


if __name__ == "__main__":
    pages = extract_text("Sample_Return_Policy.pdf")
    chunks = chunk_text(pages)

    while True:
        q = input("\nQuestion (or 'quit'): ")
        if q.strip().lower() == "quit":
            break
        print(answer_question(chunks, q))
