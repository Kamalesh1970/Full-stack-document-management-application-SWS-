from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import db
from app.config import settings
from app.routers import chat, documents
from app.services.llm import is_mock_mode


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    if is_mock_mode():
        print("LLM_API_KEY not set, chat will use mock answers")
    yield


app = FastAPI(
    title="Document Assistant API",
    version="1.0.0",
    description=(
        "Upload, list, download and delete text documents (.txt, .md, .json) and ask questions about them. "
        "Documents are ranked with BM25 and the best matches are sent to an LLM as context. "
        "Without an LLM_API_KEY the chat returns a mock answer built from the documents."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# FastAPI returns 422 with a big error list by default, a short 400 is friendlier here
@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"] if part != "body")
    message = "Request body is not valid JSON" if first["type"] == "json_invalid" else f"{field}: {first['msg']}"
    return JSONResponse(status_code=400, content={"detail": message})


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "aiProvider": "mock" if is_mock_mode() else "llm"}


app.include_router(documents.router)
app.include_router(chat.router)
