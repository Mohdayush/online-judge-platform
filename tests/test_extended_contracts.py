from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.contracts import ContestCreate, ProblemCreate, RegisterRequest, SubmissionCreate


def test_register_rejects_invalid_username():
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", username="bad-name", password="password123")


def test_submission_rejects_unknown_language():
    with pytest.raises(ValidationError):
        SubmissionCreate(problem_id=1, language="java", source_code="class Main {}")


def test_problem_limits_are_bounded():
    with pytest.raises(ValidationError):
        ProblemCreate(title="Test", slug="test", description="A sufficiently long description", difficulty="EASY", time_limit_ms=1)


def test_contest_end_must_follow_start():
    start = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        ContestCreate(title="Contest", starts_at=start, ends_at=start - timedelta(minutes=1), problems=[{"problem_id": 1}])
