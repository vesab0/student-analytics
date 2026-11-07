import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

PASSWORD = "correct-horse-battery"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def new_email() -> str:
    return f"{uuid.uuid4().hex[:12]}@example.com"


async def register_and_login(client, email=None):
    email = email or new_email()
    r = await client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201
    r = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200
    return email, r.json()["access_token"]


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok", "redis": "ok"}


async def test_register_login_me(client):
    email, token = await register_and_login(client)
    r = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == email and body["role"] == "student"
    assert "hashed_password" not in body


async def test_duplicate_register_conflict(client):
    email, _ = await register_and_login(client)
    r = await client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 409


async def test_register_rejects_short_password_and_bad_email(client):
    r = await client.post("/auth/register", json={"email": new_email(), "password": "short"})
    assert r.status_code == 422
    r = await client.post("/auth/register", json={"email": "not-an-email", "password": PASSWORD})
    assert r.status_code == 422


async def test_wrong_password_401(client):
    email, _ = await register_and_login(client)
    r = await client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert r.status_code == 401


async def test_me_without_or_with_bad_token_401(client):
    assert (await client.get("/auth/me")).status_code == 401
    r = await client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


async def test_logout_revokes_token(client):
    _, token = await register_and_login(client)
    h = {"Authorization": f"Bearer {token}"}
    assert (await client.post("/auth/logout", headers=h)).status_code == 204
    assert (await client.get("/auth/me", headers=h)).status_code == 401


async def test_student_cannot_list_users_403(client):
    _, token = await register_and_login(client)
    r = await client.get("/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


async def test_login_rate_limited_after_repeated_failures(client):
    email, _ = await register_and_login(client)
    codes = []
    for _ in range(7):
        r = await client.post("/auth/login", json={"email": email, "password": "wrong-password"})
        codes.append(r.status_code)
    assert codes[:5] == [401] * 5
    assert codes[5:] == [429, 429]
