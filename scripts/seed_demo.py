"""Seed a small local dataset for demonstrating CodeArena."""
from getpass import getpass

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models.entities import Problem, Role, TestCase, User
from app.services.auth import hash_password


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.username == "demo_admin"))
        if admin is None:
            password = getpass("Choose a password for demo_admin: ")
            if len(password) < 8:
                raise SystemExit("Password must contain at least 8 characters")
            admin = User(email="demo-admin@example.com", username="demo_admin", password_hash=hash_password(password), role=Role.ADMIN)
            db.add(admin)
            db.flush()
        problem = db.scalar(select(Problem).where(Problem.slug == "sum-two-numbers"))
        if problem is None:
            problem = Problem(
                title="Sum Two Numbers", slug="sum-two-numbers",
                description="Read two integers and print their sum.", difficulty="EASY",
                time_limit_ms=1000, memory_limit_mb=128, created_by=admin.id,
            )
            db.add(problem)
            db.flush()
            db.add_all([
                TestCase(problem_id=problem.id, input_data="2 3\n", expected_output="5\n", is_hidden=False),
                TestCase(problem_id=problem.id, input_data="100 250\n", expected_output="350\n", is_hidden=True),
            ])
        db.commit()
        print("Demo dataset ready. Sign in as demo_admin with the password you chose.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
