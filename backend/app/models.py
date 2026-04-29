from typing import Annotated

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
  username: str
  password: str


class RenameColumnRequest(BaseModel):
  title: Annotated[str, Field(max_length=255)]


class CreateCardRequest(BaseModel):
  title: Annotated[str, Field(max_length=255)]
  details: Annotated[str, Field(default="", max_length=10_000)]


class UpdateCardRequest(BaseModel):
  title: Annotated[str, Field(max_length=255)]
  details: Annotated[str, Field(max_length=10_000)]


class MoveCardRequest(BaseModel):
  column_id: str
  position: int
