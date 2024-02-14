import re

from jose import jwt
from pydantic import validate_email
from pydantic_core import PydanticCustomError

from rchat.conf import SECRET_KEY
from rchat.views.auth.models import LoginTypeEnum, Session, UserDataPatternEnum


def get_login_type(login: str) -> LoginTypeEnum | None:
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
        "exp": session.expired_at,
    }
    refresh_payload = {"refresh_id": session.refresh_id.hex}

    return {
        "access_token": jwt.encode(claims=access_payload, key=SECRET_KEY),
        "refresh_token": jwt.encode(claims=refresh_payload, key=SECRET_KEY),
    }
