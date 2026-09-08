from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Problem, Submission, User
from app.schemas.contracts import LoginRequest, ProblemCreate, ProblemResponse, RegisterRequest, SubmissionCreate, SubmissionResponse, TokenResponse
from app.services.auth import admin_user, create_access_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/api/v1")


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where((User.email == payload.email) | (User.username == payload.username)))
    if existing:
        raise HTTPException(status_code=409, detail="Email or username already exists")
    user = User(email=payload.email, username=payload.username, password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenResponse(access_token=create_access_token(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user))


@router.get("/problems", response_model=list[ProblemResponse])
def list_problems(db: Session = Depends(get_db)):
    return db.scalars(select(Problem).order_by(Problem.id)).all()


@router.post("/problems", response_model=ProblemResponse, status_code=201)
def create_problem(payload: ProblemCreate, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    if db.scalar(select(Problem).where(Problem.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="Problem slug already exists")
    problem = Problem(**payload.model_dump(), created_by=user.id)
    db.add(problem); db.commit(); db.refresh(problem)
    return problem


@router.post("/submissions", response_model=SubmissionResponse, status_code=202)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(Problem, payload.problem_id):
        raise HTTPException(status_code=404, detail="Problem not found")
    submission = Submission(**payload.model_dump(), user_id=user.id)
    db.add(submission); db.commit(); db.refresh(submission)
    # The production queue publisher is intentionally a separate worker boundary.
    return submission


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.user_id != user.id and user.role.value != "ADMIN":
        raise HTTPException(status_code=403, detail="You cannot view this submission")
    return submission
