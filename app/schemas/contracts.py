from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserStatsResponse(BaseModel):
    total_submissions: int
    accepted_submissions: int
    solved_problems: int


class ProblemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    slug: str = Field(min_length=3, max_length=200, pattern=r"^[a-z0-9-]+$")
    description: str = Field(min_length=10, max_length=50000)
    difficulty: str = Field(pattern=r"^(EASY|MEDIUM|HARD)$")
    tags: str = Field(default="", max_length=500)
    constraints: str = Field(default="", max_length=20000)
    input_format: str = Field(default="", max_length=10000)
    output_format: str = Field(default="", max_length=10000)
    editorial: str = Field(default="", max_length=50000)
    time_limit_ms: int = Field(default=1000, ge=100, le=10000)
    memory_limit_mb: int = Field(default=128, ge=16, le=1024)


class ProblemResponse(ProblemCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SubmissionCreate(BaseModel):
    problem_id: int = Field(gt=0)
    contest_id: int | None = Field(default=None, gt=0)
    language: str = Field(pattern=r"^(python|cpp)$")
    source_code: str = Field(min_length=1, max_length=50000)


class TestCaseCreate(BaseModel):
    input_data: str = Field(default="", max_length=100000)
    expected_output: str = Field(max_length=100000)
    is_hidden: bool = True


class TestCaseResponse(BaseModel):
    id: int
    problem_id: int
    is_hidden: bool
    model_config = ConfigDict(from_attributes=True)


class SubmissionResponse(BaseModel):
    id: int
    problem_id: int
    language: str
    status: str
    execution_time_ms: int | None
    memory_used_kb: int | None
    error_message: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ContestProblemCreate(BaseModel):
    problem_id: int = Field(gt=0)
    points: int = Field(default=100, ge=1, le=10000)


class ContestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    starts_at: datetime
    ends_at: datetime
    problems: list[ContestProblemCreate] = Field(min_length=1, max_length=100)

    @field_validator("ends_at")
    @classmethod
    def end_after_start(cls, value: datetime, info):
        start = info.data.get("starts_at")
        if start and value <= start:
            raise ValueError("ends_at must be after starts_at")
        return value


class ContestResponse(BaseModel):
    id: int
    title: str
    description: str
    starts_at: datetime
    ends_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    score: int
    solved: int
    penalty_seconds: int
