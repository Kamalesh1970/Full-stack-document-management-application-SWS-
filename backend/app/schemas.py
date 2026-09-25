from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str = Field(alias="_id", examples=["66f3c1a2b4d5e6f708192a3b"])
    originalName: str = Field(examples=["leave-policy.txt"])
    extension: str = Field(examples=[".txt"])
    mimeType: str = Field(examples=["text/plain"])
    size: int = Field(description="Size in bytes", examples=[1532])
    createdAt: str


class DeleteOut(BaseModel):
    message: str = "Document deleted"
    id: str = Field(alias="_id")


class ChatRequest(BaseModel):
    question: str = Field(examples=["How many days of annual leave do employees get?"])


class Source(BaseModel):
    id: str = Field(alias="_id")
    originalName: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    provider: str | None = Field(None, description='"llm" or "mock". Missing when nothing matched')


class ErrorOut(BaseModel):
    detail: str
