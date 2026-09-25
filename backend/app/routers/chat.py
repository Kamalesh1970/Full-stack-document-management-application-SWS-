from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app import db
from app.schemas import ChatRequest, ChatResponse, ErrorOut
from app.services.llm import generate_answer
from app.services.search import search

router = APIRouter(prefix="/api/chat", tags=["Chat"])

MAX_QUESTION_LENGTH = 2000


@router.post(
    "",
    response_model=ChatResponse,
    response_model_exclude_none=True,
    responses={400: {"model": ErrorOut}, 502: {"model": ErrorOut}, 503: {"model": ErrorOut}},
)
async def ask(body: ChatRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(400, "Question is required")
    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(400, f"Question is too long (max {MAX_QUESTION_LENGTH} characters)")

    documents = db.list_with_content()
    if not documents:
        return {"answer": "No documents have been uploaded yet. Upload a document first, then ask about it.", "sources": []}

    sources, context = search(question, documents)
    if not sources:
        return {"answer": "I couldn't find anything related to that in the uploaded documents.", "sources": []}

    # the llm call is blocking (httpx sync), keep it off the event loop
    answer, provider = await run_in_threadpool(generate_answer, question, context)

    return {
        "answer": answer,
        "sources": [{"_id": str(doc["_id"]), "originalName": doc["originalName"]} for doc in sources],
        "provider": provider,
    }
