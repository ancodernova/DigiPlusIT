"""Workspace and membership schemas."""

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    workspace_type: str = "organization"


class WorkspaceUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class MemberRoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|manager|member)$")


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
