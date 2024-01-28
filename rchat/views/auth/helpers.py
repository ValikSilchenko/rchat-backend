from jwt import encode

from rchat.conf import SECRET_KEY
from rchat.views.auth.models import Session


def create_token(session: Session) -> str:
    payload = {"session": session.id.hex}
    if session.user_agent:
        payload["user_agent"] = session.user_agent

    return encode(payload=payload, key=SECRET_KEY)

