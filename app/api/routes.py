from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Contest, ContestProblem, ContestRegistration, ContestSubmission, Problem, Submission, SubmissionStatus, TestCase, User
from app.schemas.contracts import ContestCreate, ContestResponse, LeaderboardEntry, LoginRequest, ProblemCreate, ProblemResponse, RegisterRequest, SubmissionCreate, SubmissionResponse, TestCaseCreate, TestCaseResponse, TokenResponse, UserResponse, UserStatsResponse
from app.services.auth import admin_user, create_access_token, current_user, hash_password, verify_password
from app.services.queue import SubmissionQueue

router = APIRouter(prefix="/api/v1")


def problem_or_404(problem_id: int, db: Session) -> Problem:
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where((User.email == email) | (User.username == payload.username))):
        raise HTTPException(status_code=409, detail="Email or username already exists")
    user = User(email=email, username=payload.username, password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenResponse(access_token=create_access_token(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user))


@router.get("/users/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return user


@router.get("/users/me/stats", response_model=UserStatsResponse)
def my_stats(db: Session = Depends(get_db), user: User = Depends(current_user)):
    total = db.scalar(select(func.count()).select_from(Submission).where(Submission.user_id == user.id)) or 0
    accepted = db.scalar(select(func.count()).select_from(Submission).where(Submission.user_id == user.id, Submission.status == SubmissionStatus.ACCEPTED)) or 0
    solved = db.scalar(select(func.count(func.distinct(Submission.problem_id))).where(Submission.user_id == user.id, Submission.status == SubmissionStatus.ACCEPTED)) or 0
    return UserStatsResponse(total_submissions=total, accepted_submissions=accepted, solved_problems=solved)


@router.get("/problems", response_model=list[ProblemResponse])
def list_problems(difficulty: str | None = Query(default=None, pattern=r"^(EASY|MEDIUM|HARD)$"), db: Session = Depends(get_db)):
    query = select(Problem).order_by(Problem.id)
    if difficulty: query = query.where(Problem.difficulty == difficulty)
    return db.scalars(query).all()


@router.get("/problems/{slug}", response_model=ProblemResponse)
def get_problem(slug: str, db: Session = Depends(get_db)):
    problem = db.scalar(select(Problem).where(Problem.slug == slug))
    if not problem: raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.post("/problems", response_model=ProblemResponse, status_code=201)
def create_problem(payload: ProblemCreate, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    if db.scalar(select(Problem).where(Problem.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="Problem slug already exists")
    problem = Problem(**payload.model_dump(), created_by=user.id)
    db.add(problem); db.commit(); db.refresh(problem)
    return problem


@router.put("/problems/{problem_id}", response_model=ProblemResponse)
def update_problem(problem_id: int, payload: ProblemCreate, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    problem = problem_or_404(problem_id, db)
    duplicate = db.scalar(select(Problem).where(Problem.slug == payload.slug, Problem.id != problem_id))
    if duplicate: raise HTTPException(status_code=409, detail="Problem slug already exists")
    for key, value in payload.model_dump().items(): setattr(problem, key, value)
    db.commit(); db.refresh(problem)
    return problem


@router.delete("/problems/{problem_id}", status_code=204)
def delete_problem(problem_id: int, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    problem = problem_or_404(problem_id, db)
    submissions = db.scalar(select(func.count()).select_from(Submission).where(Submission.problem_id == problem_id)) or 0
    contest_refs = db.scalar(select(func.count()).select_from(ContestProblem).where(ContestProblem.problem_id == problem_id)) or 0
    if submissions or contest_refs: raise HTTPException(status_code=409, detail="Cannot delete a problem with submissions or contest references")
    db.delete(problem); db.commit()


@router.post("/problems/{problem_id}/test-cases", response_model=TestCaseResponse, status_code=201)
def create_test_case(problem_id: int, payload: TestCaseCreate, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    problem_or_404(problem_id, db)
    case = TestCase(problem_id=problem_id, **payload.model_dump())
    db.add(case); db.commit(); db.refresh(case)
    return case


@router.get("/problems/{problem_id}/test-cases", response_model=list[TestCaseResponse])
def list_test_cases(problem_id: int, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    problem_or_404(problem_id, db)
    return db.scalars(select(TestCase).where(TestCase.problem_id == problem_id).order_by(TestCase.id)).all()


@router.delete("/test-cases/{test_case_id}", status_code=204)
def delete_test_case(test_case_id: int, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    case = db.get(TestCase, test_case_id)
    if not case: raise HTTPException(status_code=404, detail="Test case not found")
    db.delete(case); db.commit()


@router.get("/users/me/submissions", response_model=list[SubmissionResponse])
def my_submissions(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Submission).where(Submission.user_id == user.id).order_by(Submission.created_at.desc()).limit(limit)).all()


@router.post("/submissions", response_model=SubmissionResponse, status_code=202)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    problem_or_404(payload.problem_id, db)
    if payload.contest_id:
        contest = db.get(Contest, payload.contest_id)
        registered = db.scalar(select(ContestRegistration).where(ContestRegistration.contest_id == payload.contest_id, ContestRegistration.user_id == user.id))
        mapped = db.scalar(select(ContestProblem).where(ContestProblem.contest_id == payload.contest_id, ContestProblem.problem_id == payload.problem_id))
        if not contest or not registered or not mapped: raise HTTPException(status_code=403, detail="You are not eligible to submit this contest problem")
        now = datetime.utcnow()
        if not contest.starts_at <= now <= contest.ends_at: raise HTTPException(status_code=409, detail="Contest is not currently active")
    submission = Submission(problem_id=payload.problem_id, language=payload.language, source_code=payload.source_code, user_id=user.id)
    db.add(submission); db.commit(); db.refresh(submission)
    if payload.contest_id:
        db.add(ContestSubmission(contest_id=payload.contest_id, submission_id=submission.id)); db.commit()
    try: SubmissionQueue().enqueue(submission.id)
    except RuntimeError:
        submission.status = SubmissionStatus.SYSTEM_ERROR; submission.error_message = "Submission queue unavailable; retry submission"; db.commit()
        raise HTTPException(status_code=503, detail="Submission queue is temporarily unavailable")
    return submission


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    submission = db.get(Submission, submission_id)
    if not submission: raise HTTPException(status_code=404, detail="Submission not found")
    if submission.user_id != user.id and user.role.value != "ADMIN": raise HTTPException(status_code=403, detail="You cannot view this submission")
    return submission


@router.get("/contests", response_model=list[ContestResponse])
def list_contests(db: Session = Depends(get_db)):
    return db.scalars(select(Contest).order_by(Contest.starts_at.desc())).all()


@router.get("/contests/{contest_id}", response_model=ContestResponse)
def get_contest(contest_id: int, db: Session = Depends(get_db)):
    contest = db.get(Contest, contest_id)
    if not contest: raise HTTPException(status_code=404, detail="Contest not found")
    return contest


@router.get("/contests/{contest_id}/problems", response_model=list[ProblemResponse])
def contest_problems(contest_id: int, db: Session = Depends(get_db)):
    if not db.get(Contest, contest_id): raise HTTPException(status_code=404, detail="Contest not found")
    return db.scalars(select(Problem).join(ContestProblem, ContestProblem.problem_id == Problem.id).where(ContestProblem.contest_id == contest_id).order_by(Problem.id)).all()


@router.post("/contests", response_model=ContestResponse, status_code=201)
def create_contest(payload: ContestCreate, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    problem_ids = [item.problem_id for item in payload.problems]
    if len(problem_ids) != len(set(problem_ids)): raise HTTPException(status_code=422, detail="A problem can appear only once in a contest")
    found = db.scalars(select(Problem.id).where(Problem.id.in_(problem_ids))).all()
    if len(found) != len(problem_ids): raise HTTPException(status_code=404, detail="One or more problems do not exist")
    contest = Contest(title=payload.title, description=payload.description, starts_at=payload.starts_at, ends_at=payload.ends_at, created_by=user.id)
    db.add(contest); db.flush()
    db.add_all([ContestProblem(contest_id=contest.id, problem_id=item.problem_id, points=item.points) for item in payload.problems])
    db.commit(); db.refresh(contest)
    return contest


@router.post("/contests/{contest_id}/register", status_code=201)
def register_for_contest(contest_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(Contest, contest_id): raise HTTPException(status_code=404, detail="Contest not found")
    existing = db.scalar(select(ContestRegistration).where(ContestRegistration.contest_id == contest_id, ContestRegistration.user_id == user.id))
    if existing: return {"status": "already_registered"}
    db.add(ContestRegistration(contest_id=contest_id, user_id=user.id)); db.commit()
    return {"status": "registered"}


@router.get("/contests/{contest_id}/leaderboard", response_model=list[LeaderboardEntry])
def contest_leaderboard(contest_id: int, db: Session = Depends(get_db)):
    contest = db.get(Contest, contest_id)
    if not contest: raise HTTPException(status_code=404, detail="Contest not found")
    registrations = db.execute(select(ContestRegistration, User).join(User, User.id == ContestRegistration.user_id).where(ContestRegistration.contest_id == contest_id)).all()
    points = dict(db.execute(select(ContestProblem.problem_id, ContestProblem.points).where(ContestProblem.contest_id == contest_id)).all())
    accepted = db.execute(select(Submission, User).join(ContestSubmission, ContestSubmission.submission_id == Submission.id).join(User, User.id == Submission.user_id).where(ContestSubmission.contest_id == contest_id, Submission.status == SubmissionStatus.ACCEPTED).order_by(Submission.created_at)).all()
    scores = {u.id: {"username": u.username, "score": 0, "solved": set(), "penalty": 0} for _, u in registrations}
    for submission, user in accepted:
        entry = scores.get(user.id)
        if entry is None or submission.problem_id in entry["solved"]: continue
        entry["solved"].add(submission.problem_id); entry["score"] += points.get(submission.problem_id, 0); entry["penalty"] += max(0, int((submission.created_at - contest.starts_at).total_seconds()))
    ordered = sorted(scores.values(), key=lambda x: (-x["score"], -len(x["solved"]), x["penalty"], x["username"]))
    return [LeaderboardEntry(rank=i + 1, username=x["username"], score=x["score"], solved=len(x["solved"]), penalty_seconds=x["penalty"]) for i, x in enumerate(ordered)]
