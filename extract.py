from pypdf import PdfReader


def extract_text(path: str) -> list[dict]:
    reader = PdfReader(path)
    results = []

    for page_num, page_obj in enumerate(reader.pages, start=1):
        text = page_obj.extract_text() or ""
        results.append({"page": page_num, "text": text})
    return results


if __name__ == "__main__":
    print(extract_text("Sample_Return_Policy.pdf"))
