from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["client", "psychologist", "admin"]
PublicRole = Literal["client", "psychologist"]


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=5, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    specialization: str | None = Field(default=None, max_length=255)
    education: str | None = None
    about: str | None = None


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    role: PublicRole
    full_name: str | None = Field(default=None, max_length=255)
    specialization: str | None = Field(default=None, max_length=255)
    education: str | None = None
    about: str | None = None


class AdminUserCreate(UserCreate):
    role: Role


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    specialization: str | None = Field(default=None, max_length=255)
    education: str | None = None
    about: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: Role
    full_name: str | None = None
    specialization: str | None = None
    education: str | None = None
    about: str | None = None
    rating: float = 0
    rating_count: int = 0


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

class SlotCreate(BaseModel):
    start_at: datetime
    end_at: datetime
    specialization: str = Field(min_length=2, max_length=255)
    meeting_link: str = Field(min_length=5, max_length=500)


class SlotUpdate(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None
    specialization: str | None = Field(default=None, min_length=2, max_length=255)
    meeting_link: str | None = Field(default=None, min_length=5, max_length=500)


class SlotRead(BaseModel):
    id: int
    psychologist_id: int
    psychologist_username: str
    psychologist_full_name: str | None = None
    client_id: int | None = None
    client_username: str | None = None
    start_at: datetime
    end_at: datetime
    specialization: str
    meeting_link: str | None = None
    is_booked: bool

class NoteCreate(BaseModel):
    client_id: int | None = None
    text: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    text: str = Field(min_length=1)


class NoteRead(BaseModel):
    id: int
    author_id: int
    author_username: str
    client_id: int
    client_username: str
    kind: str
    text: str
    created_at: datetime
    updated_at: datetime


class RecommendationCreate(BaseModel):
    client_id: int
    text: str = Field(min_length=1)


class RecommendationRead(BaseModel):
    id: int
    psychologist_id: int
    psychologist_username: str
    psychologist_full_name: str | None = None
    client_id: int
    client_username: str
    text: str
    created_at: datetime


class ReviewCreate(BaseModel):
    psychologist_id: int
    rating: int = Field(ge=1, le=5)
    text: str | None = None


class ReviewRead(BaseModel):
    id: int
    psychologist_id: int
    client_id: int
    rating: int
    text: str | None = None
    created_at: datetime
