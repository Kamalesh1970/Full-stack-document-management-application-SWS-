import httpx
from fastapi import HTTPException
from app.config import settings
from app.services.search import tokenize

SYSTEM_PROMPT = (
    "You answer questions using only the documents provided. "
    "If the documents don't contain the answer, say you couldn't find it in the uploaded documents. "
    "Keep answers short and clear, and mention which document the information came from when it helps."
)


def is_mock_mode():
    return not settings.LLM_API_KEY


def build_prompt(question, context):
    docs = "\n\n".join(f'<document name="{c["name"]}">\n{c["text"]}\n</document>' for c in context)
    return f"{docs}\n\nQuestion: {question}"


def ask_llm(question, context):
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(question, context)},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}

    try:
        res = httpx.post(f"{settings.LLM_API_BASE}/chat/completions", json=payload, headers=headers, timeout=60)
    except httpx.HTTPError:
        raise HTTPException(502, "Could not reach the AI provider")

    if res.status_code == 401:
        raise HTTPException(502, "AI provider rejected the API key. Check LLM_API_KEY")
    if res.status_code == 429:
        raise HTTPException(503, "AI provider is rate limiting requests, try again shortly")
    if res.status_code >= 400:
        raise HTTPException(502, f"AI provider error ({res.status_code})")

    try:
        answer = res.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise HTTPException(502, "AI provider returned an unexpected response")

    return (answer or "").strip() or "The AI provider returned an empty answer."


# Used when no API key is set. Picks the sentences that share the most words
# with the question, so the answer still comes from the documents.
def mock_answer(question, context):
    question_words = set(tokenize(question))
    picked = []

    for c in context:
        for sentence in c["text"].replace("\n", ". ").split(". "):
            sentence = sentence.strip(" .,")
            if len(sentence) < 20:
                continue
            score = len(question_words & set(tokenize(sentence)))
            if score:
                picked.append((score, sentence, c["name"]))

    picked.sort(key=lambda item: item[0], reverse=True)
    if not picked:
        return f'[Mock answer - no API key set] The closest document is "{context[0]["name"]}", but no sentence in it matches the question closely.'

    lines = [f"- {sentence}. (from {name})" for _, sentence, name in picked[:3]]
    return "[Mock answer - no API key set] Here is what the documents say:\n" + "\n".join(lines)


def generate_answer(question, context):
    if is_mock_mode():
        return mock_answer(question, context), "mock"
    return ask_llm(question, context), "llm"
