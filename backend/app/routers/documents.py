import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app import db
from app.config import settings
from app.schemas import DeleteOut, DocumentOut, ErrorOut

router = APIRouter(prefix="/api/documents", tags=["Documents"])

ERRORS = {400: {"model": ErrorOut}, 404: {"model": ErrorOut}}


def find_document(doc_id):
    if not db.is_valid_id(doc_id):
        raise HTTPException(400, "Invalid document id")
    row = db.get_document(doc_id)
    if not row:
        raise HTTPException(404, "Document not found")
    return row


def extract_text(data, extension):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "File is not valid UTF-8 text")

    if "\x00" in text:
        raise HTTPException(400, "File looks like binary data, not text")

    if extension == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            raise HTTPException(400, "File has a .json extension but is not valid JSON")
        # pretty print so keys and values end up on their own lines for search
        return json.dumps(parsed, indent=2, ensure_ascii=False)

    return text


@router.post("", status_code=201, response_model=DocumentOut, responses={400: {"model": ErrorOut}})
async def upload_document(file: UploadFile | None = File(None)):
    if file is None or not file.filename:
        raise HTTPException(400, 'No file uploaded. Send it in a form field named "file"')

    original_name = Path(file.filename).name
    extension = Path(original_name).suffix.lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
        raise HTTPException(400, f'Unsupported file type "{extension or "none"}". Allowed: {allowed}')

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(400, f"File is too large. Max size is {settings.MAX_FILE_SIZE_MB} MB")
    if not data:
        raise HTTPException(400, "File is empty")

    content = extract_text(data, extension)

    stored_name = f"{uuid.uuid4().hex}{extension}"
    path = settings.UPLOAD_DIR / stored_name
    path.write_bytes(data)

    try:
        row = db.insert_document(
            original_name, stored_name, extension, settings.ALLOWED_EXTENSIONS[extension], len(data), content
        )
    except Exception:
        # don't leave an orphan file if the db insert failed
        path.unlink(missing_ok=True)
        raise

    return db.to_public(row)


@router.get("", response_model=list[DocumentOut])
def list_documents():
    return [db.to_public(row) for row in db.list_documents()]


@router.get("/{doc_id}", response_model=DocumentOut, responses=ERRORS)
def get_document(doc_id: str):
    return db.to_public(find_document(doc_id))


@router.get(
    "/{doc_id}/download",
    response_class=FileResponse,
    responses={200: {"description": "The original file"}, **ERRORS},
)
def download_document(doc_id: str):
    row = find_document(doc_id)
    path = settings.UPLOAD_DIR / row["storedName"]
    if not path.exists():
        raise HTTPException(404, "File for this document is missing on the server")
    return FileResponse(path, media_type=row["mimeType"], filename=row["originalName"])


@router.delete("/{doc_id}", response_model=DeleteOut, responses=ERRORS)
def delete_document(doc_id: str):
    row = find_document(doc_id)
    (settings.UPLOAD_DIR / row["storedName"]).unlink(missing_ok=True)
    db.delete_document(doc_id)
    return {"message": "Document deleted", "_id": doc_id}
