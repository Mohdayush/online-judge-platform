import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Role(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class SubmissionStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20))
    tags: Mapped[str] = mapped_column(String(500), default="")
    constraints: Mapped[str] = mapped_column(Text, default="")
    input_format: Mapped[str] = mapped_column(Text, default="")
    output_format: Mapped[str] = mapped_column(Text, default="")
    editorial: Mapped[str] = mapped_column(Text, default="")
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=1000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=128)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    language: Mapped[str] = mapped_column(String(20))
    source_code: Mapped[str] = mapped_column(Text)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.QUEUED, nullable=False)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_used_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TestCase(Base):
    __tablename__ = "test_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    input_data: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Contest(Base):
    __tablename__ = "contests"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))


class ContestProblem(Base):
    __tablename__ = "contest_problems"
    __table_args__ = (UniqueConstraint("contest_id", "problem_id", name="uq_problem_per_contest"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    points: Mapped[int] = mapped_column(Integer, default=100)


class ContestRegistration(Base):
    __tablename__ = "contest_registrations"
    __table_args__ = (UniqueConstraint("contest_id", "user_id", name="uq_user_registration_per_contest"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ContestSubmission(Base):
    __tablename__ = "contest_submissions"
    __table_args__ = (UniqueConstraint("contest_id", "submission_id", name="uq_submission_per_contest"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
