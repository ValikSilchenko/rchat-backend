import logging
import re
from datetime import datetime, timedelta

from fastapi import Header, HTTPException
from jose import JWTError, jwt
from pydantic import validate_email
from pydantic_core import PydanticCustomError
from starlette import status

from rchat.conf import SECRET_KEY, SESSION_LIFETIME_MIN
from rchat.schemas.models import Session
from rchat.state import app_state
from rchat.views.auth.models import LoginTypeEnum, UserDataPatternEnum

logger = logging.getLogger(__name__)


def get_login_type(login: str) -> LoginTypeEnum | None:
    """
    Возвращает тип логина для переданной строки.
    :param login: строка, используемая как логин пользователя
    :return: тип логина (email или public_id)
    или None при несоответствии одному из форматов
    """
    try:
        validate_email(login)
        # в случае несовпадения паттерну вызывает исключение
        return LoginTypeEnum.email
    except PydanticCustomError:
        pass

    if re.match(UserDataPatternEnum.public_id, login):
        return LoginTypeEnum.public_id


def generate_tokens(session: Session, user_public_id: str) -> dict[str, str]:
    """
    Создаёт пару токенов доступа для пользователя.
    :param session: сессия пользователя
    :param user_public_id: public_id пользователя
    :return: Словарь вида {access_token: ..., refresh_token: ...}
    """
    access_payload = {
        "session": session.id.hex,
        "public_id": user_public_id,
        "exp": session.created_timestamp
        + timedelta(minutes=SESSION_LIFETIME_MIN),
    }
    refresh_payload = {"refresh_id": session.refresh_id.hex}

    return {
        "access_token": jwt.encode(claims=access_payload, key=SECRET_KEY),
        "refresh_token": jwt.encode(claims=refresh_payload, key=SECRET_KEY),
    }


def get_decoded_token(auth_data: str) -> dict:
    """
    Получает
    :param auth_data:
    :return:
    """
    try:
        auth_type, token = auth_data.split(" ")
    except Exception:
        logger.error(
            "Invalid Authorization header format. Authorization=%s", auth_data
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if auth_type != "Bearer":
        logger.error("Auth type is invalid. auth_type=%s", auth_type)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    try:
        decoded_token = jwt.decode(
            token=token, key=SECRET_KEY, algorithms=[jwt.ALGORITHMS.HS256]
        )
    except JWTError:
        logger.error("Token decoding error.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return decoded_token


async def check_access_token(
    auth_data: str = Header(alias="Authorization"),
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
        logger.error("Session not found.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    session_expire_at = session.created_timestamp + timedelta(
        minutes=SESSION_LIFETIME_MIN
    )
    if session_expire_at < datetime.now():
        logger.error("Session expired.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired"
        )

    return session


async def check_refresh_token(
    auth_data: str = Header(alias="Authorization"),
) -> Session:
    """
    Проверяет refresh_token пользователя на валидность.
    Нужен для обновления токенов доступа.
    :raise HTTPException: в случаях невалидности токена
    """
    token = get_decoded_token(auth_data)
    session = await app_state.session_repo.get_by_refresh_id(
        refresh_id=token["refresh_id"]
    )
    if not session:
        logger.error("Session not found.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return session
