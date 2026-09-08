from app.models.entities import SubmissionStatus


def test_submission_status_includes_resource_verdicts():
    assert SubmissionStatus.MEMORY_LIMIT_EXCEEDED.value == "MEMORY_LIMIT_EXCEEDED"
    assert SubmissionStatus.TIME_LIMIT_EXCEEDED.value == "TIME_LIMIT_EXCEEDED"
