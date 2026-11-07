from fastapi import FastAPI, Response, status
from sqlalchemy import text

from app.api import auth
from app.core.redis import redis_client
from app.db.session import engine

app = FastAPI(title="Student Analytics API", version="0.1.0")
app.include_router(auth.router)


@app.get("/health", tags=["system"])
async def health(response: Response):
    checks = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "unavailable"
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"
    healthy = all(v == "ok" for v in checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if healthy else "degraded", **checks}
