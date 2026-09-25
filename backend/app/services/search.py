import math
import re

# BM25 ranking over paragraphs of every uploaded document.
# The best paragraphs become the LLM context, and their documents become the sources.

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from", "how",
    "i", "if", "in", "is", "it", "its", "me", "my", "of", "on", "or", "our", "so", "that", "the",
    "their", "there", "this", "to", "was", "we", "what", "when", "where", "which", "who", "why",
    "will", "with", "you", "your", "about", "any", "all", "am", "have", "has", "had", "tell",
    "please", "get", "much", "many",
}

MAX_CHUNK_CHARS = 1000
TOP_CHUNKS = 5
MAX_SOURCES = 3


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [stem(w) for w in words if len(w) > 1 and w not in STOP_WORDS]


def stem(word):
    # just enough so "employees" matches "employee"
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def split_chunks(text):
    chunks = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        # very long paragraphs get cut into pieces so one chunk can't eat the whole context
        while len(para) > MAX_CHUNK_CHARS:
            chunks.append(para[:MAX_CHUNK_CHARS])
            para = para[MAX_CHUNK_CHARS:]
        if para:
            chunks.append(para)
    return chunks


def bm25_scores(query_tokens, chunk_tokens, k1=1.5, b=0.75):
    n = len(chunk_tokens)
    avg_len = sum(len(t) for t in chunk_tokens) / n or 1.0

    doc_freqs = {}
    for tokens in chunk_tokens:
        for token in set(tokens):
            doc_freqs[token] = doc_freqs.get(token, 0) + 1

    scores = []
    for tokens in chunk_tokens:
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        score = 0.0
        for token in query_tokens:
            if token not in tf:
                continue
            n_q = doc_freqs[token]
            idf = math.log((n - n_q + 0.5) / (n_q + 0.5) + 1.0)
            score += idf * (tf[token] * (k1 + 1)) / (tf[token] + k1 * (1 - b + b * len(tokens) / avg_len))
        scores.append(score)
    return scores


# documents are mongo docs with _id, originalName and content
def search(question, documents):
    query_tokens = set(tokenize(question))
    if not query_tokens:
        return [], []

    chunks = []
    for doc in documents:
        # file name counts too, so "leave policy" finds leave-policy.txt
        for text in split_chunks(doc["content"]):
            chunks.append({"doc": doc, "text": text, "tokens": tokenize(doc["originalName"] + " " + text)})

    if not chunks:
        return [], []

    scores = bm25_scores(query_tokens, [c["tokens"] for c in chunks])
    ranked = sorted(zip(scores, chunks), key=lambda pair: pair[0], reverse=True)
    ranked = [(score, chunk) for score, chunk in ranked if score > 0]
    if not ranked:
        return [], []

    # ignore weak matches that only share a common word with the question
    cutoff = ranked[0][0] * 0.5
    top = [chunk for score, chunk in ranked[:TOP_CHUNKS] if score >= cutoff]

    sources = {}
    for chunk in top:
        if len(sources) < MAX_SOURCES:
            sources.setdefault(chunk["doc"]["_id"], chunk["doc"])
    sources = list(sources.values())
    source_ids = {doc["_id"] for doc in sources}

    context = [
        {"name": chunk["doc"]["originalName"], "text": chunk["text"]}
        for chunk in top
        if chunk["doc"]["_id"] in source_ids
    ]
    return sources, context
