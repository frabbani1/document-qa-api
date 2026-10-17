import uuid
from chunk import chunk_text

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

from extract import extract_text
from index import Answer, answer_question

app = FastAPI(title="Document Q/A API")
documents: dict[str, list[dict]] = {}


class AskRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=1)


@app.post("/documents")
def upload_files(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF's are allowed")
    try:
        pages = extract_text(file.file)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Could not read file as a PDF please upload another PDF",
        ) from e

    if not any(p["text"].strip() for p in pages):
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from this file, please try again",
        )
    chunk = chunk_text(pages)
    document_id = str(uuid.uuid4())
    documents[document_id] = chunk
    return {"document_id": document_id, "pages": len(pages), "passages": len(chunk)}


@app.post("/ask", response_model=Answer)
def ask(request: AskRequest):
    if request.document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    chunk = documents[request.document_id]
    return answer_question(chunk, request.question)
