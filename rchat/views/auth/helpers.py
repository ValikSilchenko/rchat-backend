import re

from jwt import encode

from rchat.conf import SECRET_KEY
from rchat.views.auth.models import Session, LoginTypeEnum, UserDataPatternEnum


def get_login_type(login: str) -> LoginTypeEnum | None:
    if re.match(UserDataPatternEnum.email, login):
        return LoginTypeEnum.email
    if re.match(UserDataPatternEnum.public_id, login):
        return LoginTypeEnum.public_id


def create_token(session: Session, user_public_id: str) -> str:
    payload = {"session": session.id.hex, "public_id": user_public_id}
    if session.user_agent:
        payload["user_agent"] = session.user_agent

    return encode(payload=payload, key=SECRET_KEY)
