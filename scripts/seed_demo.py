"""Seed a small local dataset for demonstrating CodeArena.

For a disposable local database only. Set DEMO_ADMIN_PASSWORD if you want a
known credential; otherwise a random password is generated for this run.
"""
import os
import secrets
import string

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models.entities import Problem, Role, TestCase, User
from app.services.auth import hash_password


def main() -> None:
    Base.metadata.create_all(bind=engine)
    password = os.getenv("DEMO_ADMIN_PASSWORD") or "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(20))
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.username == "demo_admin"))
        if admin is None:
            admin = User(email="demo-admin@example.com", username="demo_admin", password_hash=hash_password(password), role=Role.ADMIN)
            db.add(admin)
            db.flush()
        problem = db.scalar(select(Problem).where(Problem.slug == "sum-two-numbers"))
        if problem is None:
            problem = Problem(title="Sum Two Numbers", slug="sum-two-numbers", description="Read two integers and print their sum.", difficulty="EASY", time_limit_ms=1000, memory_limit_mb=128, created_by=admin.id)
            db.add(problem)
            db.flush()
            db.add_all([
                TestCase(problem_id=problem.id, input_data="2 3\n", expected_output="5\n", is_hidden=False),
                TestCase(problem_id=problem.id, input_data="100 250\n", expected_output="350\n", is_hidden=True),
            ])
        db.commit()
        print("Demo dataset ready. Admin username: demo_admin")
        print("Demo password for this run:", password)
        print("Do not use this account on a public deployment.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
