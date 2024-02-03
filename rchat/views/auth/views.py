import secrets
from hashlib import sha256

from fastapi import APIRouter, Header, HTTPException
from starlette import status
from starlette.responses import Response

from rchat.conf import BASE_BACKEND_URL
from rchat.state import app_state
from rchat.views.auth.helpers import create_token
from rchat.views.auth.models import AuthBody, AuthResponse, CreateUserData

router = APIRouter()


@router.get("/test")
async def test():
    secrets.token_hex(32)


@router.post("/api/auth")
async def auth(
    body: AuthBody,
    user_agent: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
):
    user = await app_state.user_repo.get_by_email(email=body.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    encrypted_password = sha256(
        string=(body.password + user.user_salt).encode()
    ).hexdigest()
    if encrypted_password != user.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    session = await app_state.session_repo.create(
        user_id=user.id, ip=x_forwarded_for, user_agent=user_agent
    )

    return AuthResponse(
        token=create_token(session - session, user_public_id=user.public_id)
    )


@router.post("/user/create")
async def create_user(auth_data: CreateUserData):
    user = await app_state.user_repo.create(
        public_id=auth_data.public_id,
        password=auth_data.password,
        email=auth_data.email,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_already_exists",
        )

    headers = {"Location": f"{BASE_BACKEND_URL}/api/auth"}
    return Response(
        content=str(
            {"email": auth_data.public_id, "password": auth_data.password}
        ),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers=headers,
    )
