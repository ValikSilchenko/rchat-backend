import logging
from typing import Optional

from fastapi import HTTPException
from pydantic import UUID5
from starlette import status

from rchat.schemas.chat import (
    Chat,
    ChatParticipant,
    ChatTypeEnum,
    UserChatRole,
)
from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.chat.models import ChatUserActionStatusEnum

logger = logging.getLogger(__name__)


async def get_chat_name_and_avatar(
    chat: Chat, user_id: UUID5
) -> tuple[str, str]:
    """
    Вспомогательный метод для получения имени чата и сслфки на его аватарку.
     - Для чата типа private название чата -
       first_name другого пользователя и его аватарка.
     - Для остальных чатов - chat.name и аватарка чата.

    :returns: кортеж вида: (chat_name, chat_avatar_url)
    """
    if chat.type == ChatTypeEnum.private:
        chat_participant = (
            await app_state.chat_repo.get_chat_participant_users(
                chat_id=chat.id
            )
        )
        other_user_id = (
            chat_participant[0]
            if chat_participant[0] != user_id
            else chat_participant[1]
        )
        other_user = await app_state.user_repo.get_by_id(id_=other_user_id)
        chat_avatar = (
            app_state.media_repo.get_media_url(id_=other_user.avatar_photo_id)
            if other_user.avatar_photo_id
            else None
        )
        return other_user.first_name, chat_avatar

    assert chat.name

    chat_avatar = (
        app_state.media_repo.get_media_url(id_=chat.avatar_photo_id)
        if chat.avatar_photo_id
        else None
    )
    return chat.name, chat_avatar


async def get_group_chat_with_user(
    chat_id: str, session: Session
) -> tuple[Chat, ChatParticipant]:
    """
    :raises HTTPException: Если чат или пользователь в этом чате не найден.
    """
    chat = await app_state.chat_repo.get_by_id(id_=chat_id)
    if not chat or chat.type != ChatTypeEnum.group:
        logger.error(
            "Group chat not found. chat_id=%s, session=%s",
            chat_id,
            session.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatUserActionStatusEnum.chat_not_found,
        )
    user_in_chat = await app_state.chat_repo.get_user_in_chat(
        chat_id=chat.id, user_id=session.user_id, chat_type=ChatTypeEnum.group
    )
    if not user_in_chat:
        logger.error(
            "Group chat with user not found. chat_id=%s, session=%s",
            chat.id,
            session.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatUserActionStatusEnum.chat_not_found,
        )
    return chat, user_in_chat


async def check_permissions_to_add(
    user_who_add: ChatParticipant,
    user_in_chat: Optional[ChatParticipant],
    new_user_role: UserChatRole,
) -> bool:
    is_forbidden = False
    if not user_in_chat and new_user_role not in {
        UserChatRole.member,
        UserChatRole.observer,
    }:
        is_forbidden = True

    match user_who_add.role:
        case UserChatRole.observer:
            is_forbidden = True
        case UserChatRole.member:
            if user_in_chat:
                is_forbidden = True
        case UserChatRole.admin:
            if user_in_chat and user_in_chat.role in {
                UserChatRole.admin,
                UserChatRole.owner,
            }:
                is_forbidden = True
            elif user_in_chat and new_user_role not in {
                UserChatRole.member,
                UserChatRole.observer,
            }:
                is_forbidden = True

    return not is_forbidden
