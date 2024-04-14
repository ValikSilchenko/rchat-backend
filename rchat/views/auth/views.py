import logging
from hashlib import sha256

from fastapi import APIRouter, Depends, Header, HTTPException
from starlette import status

from rchat.schemas.models import Session
from rchat.state import app_state
from rchat.views.auth.helpers import (
    check_refresh_token,
    generate_tokens,
    get_login_type,
)
from rchat.views.auth.models import (
    AuthBody,
    AuthResponse,
    CreateUserData,
    LoginTypeEnum,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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
    login_type = get_login_type(login=body.login)

    match login_type:
        case LoginTypeEnum.email:
            user = await app_state.user_repo.get_by_email(email=body.login)
        case LoginTypeEnum.public_id:
            user = await app_state.user_repo.get_by_public_id(
                public_id=body.login
            )
        case _:
            logger.error("Invalid login type. login=%s", body.login)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if not user:
        logger.error(
            "User not found. login_type=%s, login=%s", login_type, body.login
        )
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

    tokens = generate_tokens(session=session, user_public_id=user.public_id)
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
    tokens = generate_tokens(
        session=new_session, user_public_id=user.public_id
    )
    return AuthResponse(**tokens)
