import logging

from fastapi import APIRouter, Depends

from rchat.clients.socketio_client import SocketioEventsEnum, sio
from rchat.schemas.chat import ChatTypeEnum
from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.chat.helpers import get_chat_name
from rchat.views.chat.models import (
    AddedInChatInfo,
    ChatListItem,
    ChatListResponse,
    CreateGroupChatBody,
    CreateGroupChatResponse,
    CreateGroupChatStatusEnum,
    GroupChatInfo,
    LastChatMessage,
)
from rchat.views.message.helpers import get_message_sender

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


@router.get(path="/chat/list", response_model=ChatListResponse)
async def get_chat_list(session: Session = Depends(check_access_token)):
    """
    Получает список чатов пользователя,
    отсортированный по времени последнего сообщения в чатах.
    """
    user_chats = await app_state.chat_repo.get_user_chats(
        user_id=session.user_id
    )
    chat_list = []
    for chat in user_chats:
        last_chat_message = await app_state.message_repo.get_last_chat_message(
            chat_id=chat.id
        )
        avatar_url = (
            app_state.media_repo.get_media_url(chat.avatar_photo_id)
            if chat.avatar_photo_id
            else None
        )
        chat_list.append(
            ChatListItem(
                id=chat.id,
                name=await get_chat_name(chat=chat, user_id=session.user_id),
                type=chat.type,
                is_work_chat=chat.is_work_chat,
                last_message=(
                    LastChatMessage(
                        id=last_chat_message.id,
                        message_type=last_chat_message.type,
                        message_text=last_chat_message.message_text,
                        created_at=last_chat_message.created_timestamp,
                        sender=await get_message_sender(last_chat_message),
                    )
                    if last_chat_message
                    else None
                ),
                avatar_photo_url=avatar_url,
            )
        )

    return ChatListResponse(chat_list=chat_list)


@router.post(path="/chat/create", response_model=CreateGroupChatResponse)
async def create_group_chat(
    group_chat_info: CreateGroupChatBody,
    session: Session = Depends(check_access_token),
):
    not_found_users = []
    for user_id in group_chat_info.user_ids:
        user = await app_state.user_repo.get_by_id(id_=user_id)
        if not user:
            not_found_users.append(user_id)
    if not_found_users:
        logger.error(
            "Some users not found. not_found_users=%s, chat_owner=%s",
            not_found_users,
            session.user_id,
        )
        return CreateGroupChatResponse(
            status=CreateGroupChatStatusEnum.users_not_found,
            users_not_found=not_found_users,
            chat_id=None,
        )

    chat = await app_state.chat_repo.create_chat(
        chat_type=ChatTypeEnum.group,
        chat_name=group_chat_info.name,
        description=group_chat_info.description,
        is_work_chat=group_chat_info.is_work_chat,
        allow_messages_from=group_chat_info.allow_messages_from,
        allow_messages_to=group_chat_info.allow_messages_to,
    )

    owner_user = await app_state.user_repo.get_by_id(id_=session.user_id)
    for user_id in group_chat_info.user_ids:
        await app_state.chat_repo.add_chat_participant(
            chat_id=chat.id, user_id=user_id, added_by_user=owner_user.id
        )
        added_in_chat_data = AddedInChatInfo(
            chat_info=GroupChatInfo(
                id=chat.id,
                name=chat.name,
                is_work_chat=chat.is_work_chat,
                avatar_photo_url=None,
                created_at=chat.created_timestamp,
            ),
            user_who_added=owner_user.first_name,
        )

        if user_id in sio.users:
            sio.emit(
                event=SocketioEventsEnum.added_in_chat,
                data=added_in_chat_data.model_dump(),
                to=sio.users[user_id],
            )

    await app_state.chat_repo.add_chat_participant(
        chat_id=chat.id, user_id=owner_user.id, is_chat_owner=True
    )

    return CreateGroupChatResponse(chat_id=chat.id, users_not_found=[])
