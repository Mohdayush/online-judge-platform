"""Run as a separate process: python -m app.workers.submission_worker."""
import logging
import time

from app.core.database import Base, SessionLocal, engine
from app.models.entities import Problem, Submission, SubmissionStatus, TestCase
from app.services.queue import SubmissionQueue
from app.services.sandbox import DockerSandbox, outputs_match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_submission(submission_id: int, sandbox: DockerSandbox | None = None) -> None:
    sandbox = sandbox or DockerSandbox()
    db = SessionLocal()
    try:
        submission = db.get(Submission, submission_id)
        if not submission or submission.status != SubmissionStatus.QUEUED:
            return
        problem = db.get(Problem, submission.problem_id)
        test_cases = db.query(TestCase).filter(TestCase.problem_id == submission.problem_id).order_by(TestCase.id).all()
        if not problem or not test_cases:
            submission.status = SubmissionStatus.SYSTEM_ERROR
            submission.error_message = "Problem has no configured test cases"
            db.commit()
            return
        submission.status = SubmissionStatus.RUNNING
        db.commit()
        for test_case in test_cases:
            result = sandbox.execute(submission.language, submission.source_code, test_case.input_data, problem.time_limit_ms, problem.memory_limit_mb)
            submission.execution_time_ms = result.execution_time_ms
            if result.verdict != "OK":
                submission.status = SubmissionStatus(result.verdict)
                submission.error_message = result.stderr
                db.commit()
                return
            if not outputs_match(result.stdout, test_case.expected_output):
                submission.status = SubmissionStatus.WRONG_ANSWER
                submission.error_message = "Output did not match expected result"
                db.commit()
                return
        submission.status = SubmissionStatus.ACCEPTED
        submission.error_message = None
        db.commit()
    except Exception:
        logger.exception("Submission %s failed", submission_id)
        if 'submission' in locals() and submission:
            submission.status = SubmissionStatus.SYSTEM_ERROR
            submission.error_message = "Worker failed; consult server logs"
            db.commit()
    finally:
        db.close()


def main() -> None:
    # Local convenience; production replaces this with versioned migrations.
    Base.metadata.create_all(bind=engine)
    queue = SubmissionQueue()
    while True:
        try:
            submission_id = queue.dequeue()
            if submission_id is not None:
                process_submission(submission_id)
        except RuntimeError:
            logger.exception("Queue connection failed; retrying")
            time.sleep(3)


if __name__ == "__main__":
    main()
