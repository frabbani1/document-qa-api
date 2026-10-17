import io
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter

import main
from index import Answer

client = TestClient(main.app)
SAMPLE_PDF = Path(__file__).parent / "Sample_Return_Policy.pdf"


def make_blank_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_upload_rejects_non_pdf():
    response = client.post(
        "/documents", files={"file": ("notes.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 400


def test_upload_rejects_pdf_with_no_text():
    response = client.post(
        "/documents", files={"file": ("blank.pdf", make_blank_pdf(), "application/pdf")}
    )
    assert response.status_code == 422


def test_ask_unknown_document():
    response = client.post("/ask", json={"document_id": "nope", "question": "hi"})
    assert response.status_code == 404


def test_ask_empty_question():
    response = client.post("/ask", json={"document_id": "anything", "question": ""})
    assert response.status_code == 422


def test_upload_then_ask(monkeypatch):
    # fake model so the test is free, fast, and doesn't need internet
    def fake_answer_question(passages, question):
        return Answer(answer="90 days", page=1)

    monkeypatch.setattr(main, "answer_question", fake_answer_question)

    with open(SAMPLE_PDF, "rb") as f:
        upload = client.post(
            "/documents", files={"file": ("policy.pdf", f, "application/pdf")}
        )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    response = client.post(
        "/ask", json={"document_id": document_id, "question": "How long to return?"}
    )
    assert response.status_code == 200
    assert response.json() == {"answer": "90 days", "page": 1}