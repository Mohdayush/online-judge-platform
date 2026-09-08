from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProblemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    description: str = Field(min_length=10)
    difficulty: str = Field(pattern=r"^(EASY|MEDIUM|HARD)$")
    time_limit_ms: int = Field(default=1000, ge=100, le=10000)
    memory_limit_mb: int = Field(default=128, ge=16, le=1024)


class ProblemResponse(ProblemCreate):
    id: int
    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    problem_id: int
    language: str = Field(pattern=r"^(python|cpp)$")
    source_code: str = Field(min_length=1, max_length=50000)


class SubmissionResponse(BaseModel):
    id: int
    problem_id: int
    language: str
    status: str
    execution_time_ms: int | None
    memory_used_kb: int | None
    error_message: str | None
    created_at: datetime
    class Config:
        from_attributes = True
