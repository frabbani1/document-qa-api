from extract import extract_text


def chunk_text(page_texts: list[dict], size: int = 80, overlap: int = 20) -> list[dict]:
    passages = []
    for p in page_texts:
        start = 0
        words = p["text"].split()

        while start < len(words):
            chunk = words[start : start + size]
            passages.append({"page": p["page"], "text": " ".join(chunk)})
            if start + size >= len(words):
                break
            start += size - overlap

    return passages


if __name__ == "__main__":
    pages = extract_text("Sample_Return_Policy.pdf")
    print(chunk_text(pages))
