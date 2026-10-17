import re
from chunk import chunk_text

from extract import extract_text

STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "of",
    "to",
    "do",
    "i",
    "my",
    "for",
    "and",
    "in",
    "on",
    "how",
    "what",
    "can",
    "does",
    "it",
    "be",
    "or",
    "at",
    "by",
    "with",
    "if",
    "you",
    "your",
    "we",
    "our",
    "this",
    "that",
}


def tokenize(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS}


def score_passages(passages: list[dict], question: str, k: int = 3) -> list[dict]:
    question_token = tokenize(question)
    scored = []
    for p in passages:
        score = len(question_token & tokenize(p["text"]))
        scored.append((score, p))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [p for score, p in scored[:k] if score > 0]


if __name__ == "__main__":
    pages = extract_text("Sample_Return_Policy.pdf")
    chunks = chunk_text(pages)

    for p in score_passages(chunks, "How long do I have to return an item?"):
        print(p["page"], " | ", p["text"][:120])
