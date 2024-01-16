from fastapi import APIRouter, Header, HTTPException

from rchat.state import app_state
from rchat.views.auth.models import AuthBody

router = APIRouter()


@router.post("/api/auth")
async def auth(
        body: AuthBody,
        user_agent: str | None = Header(default=None),
        x_forwarded_for: str | None = Header(default=None)
):
    user = await app_state.user_repo.get_by_login(body.login)
    print(user, body.login)
    if not user:
        raise HTTPException(status_code=404)

    session = await app_state.session_repo.create(user.id, x_forwarded_for, user_agent)
    return {"jwt": session.id}
