"""Create (or promote) an admin user. Runs on container start.

Uses ADMIN_EMAIL / ADMIN_PASSWORD env vars, defaulting to admin@edustat.com / admin123.

Usage: docker compose exec api python -m app.scripts.create_admin
"""
import asyncio
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

DEFAULT_EMAIL = "admin@edustat.com"
DEFAULT_PASSWORD = "admin123"


async def main() -> None:
    email = os.environ.get("ADMIN_EMAIL") or DEFAULT_EMAIL
    password = os.environ.get("ADMIN_PASSWORD") or DEFAULT_PASSWORD
    email = email.lower()
    async with SessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user:
            user.role = "admin"
            print(f"Promoted existing user {email} to admin")
        else:
            db.add(User(email=email, hashed_password=hash_password(password), role="admin"))
            print(f"Created admin {email}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
