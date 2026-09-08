"""Create or promote a local CodeArena administrator.

Usage:
  python -m scripts.bootstrap_admin admin@example.com adminuser

The password is requested interactively so it is not stored in shell history.
"""
import getpass
import sys

from app.core.database import Base, SessionLocal, engine
from app.models.entities import Role, User
from app.services.auth import hash_password
from sqlalchemy import select


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m scripts.bootstrap_admin EMAIL USERNAME")
    email, username = sys.argv[1:]
    password = getpass.getpass("Admin password: ")
    if len(password) < 8:
        raise SystemExit("Password must contain at least 8 characters")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, username=username, password_hash=hash_password(password), role=Role.ADMIN)
            db.add(user)
        else:
            user.role = Role.ADMIN
            user.password_hash = hash_password(password)
        db.commit()
        print(f"Admin ready: {user.username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
