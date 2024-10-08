import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Header, HTTPException
from jose import JWTError, jwt
from pydantic import validate_email
from pydantic_core import PydanticCustomError
from starlette import status

from rchat.conf import REFRESH_LIFETIME_DAYS, SECRET_KEY, SESSION_LIFETIME_MIN
from rchat.schemas.session import Session
from rchat.schemas.user import User
from rchat.state import app_state
from rchat.views.auth.models import UserDataPatternEnum

logger = logging.getLogger(__name__)


async def get_user_by_login(login: str) -> Optional[User]:
    """
    Возвращет пользователя по логину.
    Если логин неверный или пользователь не найден, возвращается None.
    """
    user = None
    try:
        validate_email(login)
        # в случае несовпадения паттерну вызывает исключение
        user = await app_state.user_repo.get_by_email(email=login)
    except PydanticCustomError:
        pass

    if re.match(UserDataPatternEnum.public_id, login):
        user = await app_state.user_repo.get_by_public_id(public_id=login)

    return user


def generate_tokens(session: Session, user: User) -> dict[str, str]:
    """
    Создаёт пару токенов доступа для пользователя.
    :return: Словарь вида {access_token: ..., refresh_token: ...}
    """
    access_payload = {
        "session": str(session.id),
        "public_id": user.public_id,
        "user_id": str(session.user_id),
        "first_name": user.first_name,
        "exp": session.created_timestamp
        + timedelta(minutes=SESSION_LIFETIME_MIN),
        "token_type": "access",
    }
    refresh_payload = {
        "session": session.id.hex,
        "exp": session.created_timestamp
        + timedelta(days=REFRESH_LIFETIME_DAYS),
        "token_type": "refresh",
    }

    return {
        "access_token": jwt.encode(claims=access_payload, key=SECRET_KEY),
        "refresh_token": jwt.encode(claims=refresh_payload, key=SECRET_KEY),
    }


def get_decoded_token(auth_data: str) -> dict:
    """
    Получает payload из Bearer JWT токена.
    :param auth_data: строка заголовка Authorizartion
    :return: payload токена из заголовка
    :raise HTTPException: в случае ошибок при декодировании токена
    """
    try:
        auth_type, token = auth_data.split(" ")
    except Exception:
        logger.error(
            "Invalid Authorization header format. auth_data=%s", auth_data
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if auth_type != "Bearer":
        logger.error("Auth type is invalid. auth_type=%s", auth_type)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    try:
        decoded_token = jwt.decode(
            token=token,
            key=SECRET_KEY,
            algorithms=[jwt.ALGORITHMS.HS256],
            options={"verify_exp": False},
        )
    except JWTError:
        logger.error("Token decoding error. token=%s", token)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return decoded_token


async def check_access_token(
    auth_data: str = Header(alias="Authorization"),
    device_fingerprint: str | None = Header(
        alias="Fingerprint-ID", default=None
    ),
) -> Session:
    """
    Проверяет access_token пользователя на валидность.
    Для валидного токена возвращает Session.
    :return: Модель сессии пользователя в случае валидного токена
    :raise HTTPException: в случаях невалидности токена
    """
    token = get_decoded_token(auth_data)

    session = await app_state.session_repo.get_by_id(token["session"])
    if not session:
        logger.error("Session not found. token_data=%s", token)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    session_expire_at = session.created_timestamp + timedelta(
        minutes=SESSION_LIFETIME_MIN
    )
    if session_expire_at < datetime.now():
        logger.error("Session expired. session_id=%s", session.id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if session.device_fingerprint != device_fingerprint:
        logger.error(
            "Device fingerprint mismatch."
            " session_id=%s, fingerprint_header=%s",
            session.id,
            device_fingerprint,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return session


async def check_refresh_token(
    auth_data: str = Header(alias="Authorization"),
    device_fingerprint: str | None = Header(
        alias="Fingerprint-ID", default=None
    ),
) -> Session:
    """
    Проверяет refresh_token пользователя на валидность.
    Нужен для обновления токенов доступа.
    :raise HTTPException: в случаях невалидности токена
    """
    token = get_decoded_token(auth_data)
    session = await app_state.session_repo.get_by_id(id_=token["session"])
    if not session:
        logger.error("Session not found. token_data=%s", token)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token_expire_at = session.created_timestamp + timedelta(
        days=REFRESH_LIFETIME_DAYS
    )
    if token_expire_at < datetime.now():
        logger.error("Refresh token expired. session_id=%s", session.id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if session.device_fingerprint != device_fingerprint:
        logger.error(
            "Device fingerprint mismatch."
            " session_id=%s, fingerprint_header=%s",
            session.id,
            device_fingerprint,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return session
