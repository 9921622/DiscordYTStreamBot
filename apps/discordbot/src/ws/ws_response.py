from pydantic import BaseModel


class WSResponse(BaseModel):
    type: str
    success: bool
    data: dict | None = None
    error: dict | None = None
