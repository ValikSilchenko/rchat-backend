import re

from jose import jwt

from rchat.conf import SECRET_KEY
from rchat.views.auth.models import Session, LoginTypeEnum, UserDataPatternEnum


def get_login_type(login: str) -> LoginTypeEnum | None:
    if re.match(UserDataPatternEnum.email, login):
        return LoginTypeEnum.email
    if re.match(UserDataPatternEnum.public_id, login):
        return LoginTypeEnum.public_id


def generate_tokens(session: Session, user_public_id: str) -> dict[str, str]:
    """
    Создаёт пару токенов доступа для пользователя.
    :param session: сессия пользователя
    :param user_public_id: public_id пользователя
    :return: Словарь вида {access_token: ..., refresh_token: ...}
    """
    access_payload = {"session": session.id.hex, "public_id": user_public_id}
    refresh_payload = {"refresh_id": session.refresh_id.hex}

    return {
        "access_token": jwt.encode(claims=access_payload, key=SECRET_KEY),
        "refresh_token": jwt.encode(claims=refresh_payload, key=SECRET_KEY),
    }
