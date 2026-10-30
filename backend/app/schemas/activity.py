"""Activity and notification schemas."""

from pydantic import BaseModel


class MemberAdd(BaseModel):
    email: str
    role: str = "member"
