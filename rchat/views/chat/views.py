import logging

from fastapi import APIRouter, Depends

from rchat.schemas.chat import ChatCreate, ChatTypeEnum
from rchat.schemas.message import MessageCreate, MessageTypeEnum
from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.chat.helpers import get_chat_name
from rchat.views.chat.models import (
    ChatListItem,
    ChatListResponse,
    CreateGroupChatBody,
    CreateGroupChatResponse,
    CreateGroupChatStatusEnum,
    LastChatMessage,
)
from rchat.views.message.helpers import (
    create_and_send_message,
    get_message_sender,
)
from rchat.views.message.models import UserCreatedChat

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


@router.post(path="/chat/create_group", response_model=CreateGroupChatResponse)
async def create_group_chat(
    group_chat_info: CreateGroupChatBody,
    session: Session = Depends(check_access_token),
):
    owner_user = await app_state.user_repo.get_by_id(id_=session.user_id)
    not_found_users = []
    user_first_names = owner_user.first_name
    for i, user_id in enumerate(group_chat_info.user_id_list):
        user = await app_state.user_repo.get_by_id(id_=user_id)
        if not user:
            not_found_users.append(user_id)
        if i < 4:
            user_first_names += f", {user.first_name}"

    if not_found_users:
        logger.error(
            "Some users not found. not_found_users=%s, chat_owner=%s",
            not_found_users,
            owner_user.id,
        )
        return CreateGroupChatResponse(
            status=CreateGroupChatStatusEnum.users_not_found,
            users_not_found=not_found_users,
        )

    chat_name = (
        group_chat_info.name if group_chat_info.name else user_first_names
    )
    create_model = ChatCreate(
        type=ChatTypeEnum.group,
        name=chat_name,
        created_by=owner_user.id,
        description=group_chat_info.description,
        is_work_chat=group_chat_info.is_work_chat,
        allow_messages_from=group_chat_info.allow_messages_from,
        allow_messages_to=group_chat_info.allow_messages_to,
    )
    chat = await app_state.chat_repo.create_chat(create_model=create_model)

    for user_id in group_chat_info.user_id_list:
        await app_state.chat_repo.add_chat_participant(
            chat_id=chat.id, user_id=user_id, added_by_user=owner_user.id
        )

    await app_state.chat_repo.add_chat_participant(
        chat_id=chat.id, user_id=owner_user.id, is_chat_owner=True
    )

    message_create_model = MessageCreate(
        type=MessageTypeEnum.created_chat,
        chat_id=chat.id,
        sender_chat_id=chat.id,
    )
    await create_and_send_message(
        message_create=message_create_model,
        chat=chat,
        chat_created_by=UserCreatedChat(
            id=owner_user.id, first_name=owner_user.first_name
        ),
    )

    return CreateGroupChatResponse(
        chat_id=chat.id,
        chat_name=chat.name,
        is_work_chat=chat.is_work_chat,
        users_not_found=[],
    )
