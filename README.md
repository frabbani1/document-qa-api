# Document Q&A API

A small FastAPI service that answers questions about a PDF. Upload a PDF, ask a question, and get back an answer with the page it came from. If the document doesn't cover the question, it says so instead of guessing.

Built by Faiz Rabbani.

## What it does

- `POST /documents` uploads a PDF and returns a `document_id`.
- `POST /ask` takes a `document_id` and a question and returns `{"answer": "...", "page": N}`.
- It refuses clearly when a file isn't a PDF, when a PDF has no extractable text (for example a scan), when the document ID is unknown, or when the question is empty.

## Quick start (about 5 minutes)

You need [Docker](https://www.docker.com/) running (Docker Desktop, or Colima on Mac) and a free NVIDIA API key from [build.nvidia.com](https://build.nvidia.com).

1. Clone the repo and go into the folder:
```
   git clone <your-repo-url>
   cd document_qa_api
```
2. Create a file named `.env` in that folder with your key:
```
   NVIDIA_API_KEY=your-key-here
```
3. Start the API:
```
   docker compose up --build
```
4. When you see `Uvicorn running on http://0.0.0.0:8000`, the API is ready at `http://127.0.0.1:8000`.

## Try it

A sample PDF (`Sample_Return_Policy.pdf`) is included.

**1. Upload the PDF:**
```
curl -X POST http://127.0.0.1:8000/documents -F "file=@Sample_Return_Policy.pdf"
```
It returns a `document_id`, plus the number of pages and passages found.

**2. Ask a question** (use your own ID):
```
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"document_id": "PASTE-ID-HERE", "question": "How long do I have to return a damaged item?"}'
```

Example response:
```json
{"answer": "90 days", "page": 1}
```

If the document doesn't cover the question, you get an answer saying it couldn't find it, and no page citation.

You can also try it in the browser at `http://127.0.0.1:8000/docs`, which lists both endpoints with forms to fill in.

## Error responses

| Situation | Status |
|---|---|
| Uploaded file is not a PDF, or can't be read as one | 400 |
| PDF has no extractable text (likely a scan) | 422 |
| Unknown `document_id` | 404 |
| Empty question | 422 |

## How it works

1. **Extract:** `pypdf` reads the text of each page.
2. **Chunk:** each page is split into overlapping passages of about 80 words, and each passage keeps its page number.
3. **Retrieve:** passages are scored by how many question words they contain (stop words ignored), and the top few are kept.
4. **Answer:** the passages are sent to the model (`openai/gpt-oss-20b` through NVIDIA's OpenAI-compatible API), which must reply in JSON.
5. **Validate:** the reply is parsed into a typed `Answer` object, and the cited page must be one of the pages sent to the model. Otherwise the answer is refused.

## Run the tests

The tests use a fake model, so they need no API key or internet.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Project layout

| File | Purpose |
|---|---|
| `main.py` | FastAPI app and endpoints |
| `extract.py` | PDF text extraction |
| `chunk.py` | Splits pages into passages |
| `retrieve.py` | Finds the most relevant passages |
| `index.py` | Model call and the typed `Answer` |
| `test_api.py` | Tests |
| `Dockerfile`, `docker-compose.yml` | Container setup |

## Limitations

- Documents are stored in memory, so they are lost when the server restarts.
- Retrieval matches exact words only, so a question phrased very differently from the document may miss. Embeddings would improve this.
- Scanned PDFs are refused because there is no OCR.
- One question is answered from the top few passages, so it can't combine information from many pages.