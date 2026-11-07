import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_token_payload, require_role
from app.core.config import settings
from app.core.redis import get_redis
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when the email is unknown, so response time doesn't reveal which emails exist.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    # Self-registration always creates a 'student'. Elevated roles are assigned by an admin.
    user = User(email=body.email.lower(), hashed_password=hash_password(body.password), role="student")
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    return user


@router.post("/login", response_model=Token)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    email = body.email.lower()
    ip = request.client.host if request.client else "unknown"
    fail_key = f"login_fail:{ip}:{email}"

    attempts = int(await redis.get(fail_key) or 0)
    if attempts >= settings.login_max_attempts:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many failed attempts, try later")

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    ok = verify_password(body.password, user.hashed_password if user else _DUMMY_HASH)
    if not (user and ok and user.is_active):
        pipe = redis.pipeline()
        pipe.incr(fail_key)
        pipe.expire(fail_key, settings.login_window_seconds)
        await pipe.execute()
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await redis.delete(fail_key)
    token, _, ttl = create_access_token(user.id, user.role)
    return Token(access_token=token, expires_in=ttl)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: dict = Depends(get_token_payload), redis: Redis = Depends(get_redis)):
    remaining = max(int(payload["exp"] - time.time()), 1)
    await redis.set(f"denylist:{payload['jti']}", "1", ex=remaining)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_role("admin"))])
async def list_users(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(User).order_by(User.id))).scalars().all()
