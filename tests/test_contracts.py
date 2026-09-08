from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.contracts import ContestCreate, ProblemCreate, SubmissionCreate


def test_submission_contract_rejects_unknown_language():
    with pytest.raises(ValidationError):
        SubmissionCreate(problem_id=1, language="java", source_code="class Main {}")


def test_problem_contract_rejects_invalid_difficulty():
    with pytest.raises(ValidationError):
        ProblemCreate(title="Test", slug="test", description="Long enough description", difficulty="UNKNOWN")


def test_contest_requires_end_after_start():
    start = datetime.utcnow()
    with pytest.raises(ValidationError):
        ContestCreate(title="Contest", starts_at=start, ends_at=start, problems=[{"problem_id": 1, "points": 100}])
