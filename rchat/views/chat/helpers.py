from pydantic import UUID5

from rchat.schemas.models import Chat, ChatTypeEnum
from rchat.state import app_state


async def get_chat_name(chat: Chat, user_id: UUID5) -> str:
    if chat.type == ChatTypeEnum.private:
        chat_participant = await app_state.chat_repo.get_chat_participant_users(
            chat_id=chat.id
        )
        other_user_id = chat_participant[0] if chat_participant[0] != user_id else chat_participant[1]
        other_user = await app_state.user_repo.get_by_id(id_=other_user_id)
        return other_user.first_name

    assert chat.name
    return chat.name

