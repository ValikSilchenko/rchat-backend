import logging
from hashlib import sha256

from fastapi import APIRouter, Depends, Header, HTTPException
from starlette import status

from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.auth.helpers import (
    check_refresh_token,
    generate_tokens,
    get_user_by_login,
)
from rchat.views.auth.models import AuthBody, AuthResponse, CreateUserData

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"])


@router.post("/api/auth", response_model=AuthResponse)
async def auth(
    body: AuthBody,
    user_agent: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
):
    """
    Метод аутентификации пользователя.
    :param body: данные для аутентификации
    :param user_agent:
    :param x_forwarded_for:
    :return: токены доступа и обновления (access_token и refresh_token)
    """
    user = await get_user_by_login(login=body.login)

    if not user:
        logger.error("User not found. login=%s", body.login)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    encrypted_password = sha256(
        string=(body.password + user.user_salt).encode()
    ).hexdigest()
    if encrypted_password != user.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    client_ip = None
    if x_forwarded_for:
        # получение ip клиента из запроса, прошедшего через прокси
        client_ip = x_forwarded_for.split(",")[0]
        await app_state.geoip_repo.get_data_by_ip(ip=client_ip)

    session = await app_state.session_repo.create(
        user_id=user.id, ip=client_ip, user_agent=user_agent
    )

    tokens = generate_tokens(session=session, user=user)
    return AuthResponse(**tokens)


@router.post("/user/create")
async def create_user(user_data: CreateUserData):
    """
    Метод создания пользователя в базе.
    :param user_data: данные для регистрации пользователя
    """
    user = await app_state.user_repo.create(
        first_name=user_data.first_name,
        public_id=user_data.public_id,
        password=user_data.password,
        email=user_data.email,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_already_exists",
        )


@router.put("/api/refresh_tokens", response_model=AuthResponse)
async def update_tokens(session: Session = Depends(check_refresh_token)):
    new_session = await app_state.session_repo.create(
        user_id=session.user_id, ip=session.ip, user_agent=session.user_agent
    )
    await app_state.session_repo.delete_session(session_id=session.id)

    user = await app_state.user_repo.get_by_id(id_=session.user_id)
    tokens = generate_tokens(session=new_session, user=user)
    return AuthResponse(**tokens)
