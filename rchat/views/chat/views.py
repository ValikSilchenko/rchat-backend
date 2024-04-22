import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from starlette import status

from rchat.schemas.chat import (
    ChatCreate,
    ChatTypeEnum,
    UserChatRole,
    UserCreatedChat,
)
from rchat.schemas.message import MessageCreate, MessageTypeEnum
from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.chat.helpers import get_chat_name_and_avatar, is_group_chat_with_user_exists
from rchat.views.chat.models import (
    BaseChatInfo,
    ChatListItem,
    ChatListResponse,
    ChatUser,
    CreateGroupChatBody,
    CreateGroupChatResponse,
    CreateGroupChatStatusEnum,
    GetChatUsersResponse,
    LastChatMessage, AddRemoveUserFromChatBody, ChatUserActionStatusEnum,
)
from rchat.views.message.helpers import (
    create_and_send_message,
    get_message_sender,
)

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
        chat_data = await get_chat_name_and_avatar(
            chat=chat, user_id=session.user_id
        )
        user_created_chat = None
        if chat.type != ChatTypeEnum.private:
            user = await app_state.user_repo.get_by_id(id_=chat.created_by)
            if user:
                user_created_chat = UserCreatedChat(
                    id=user.id, first_name=user.first_name
                )

        chat_list.append(
            ChatListItem(
                id=chat.id,
                name=chat_data[0],
                type=chat.type,
                is_work_chat=chat.is_work_chat,
                allow_messages_from=chat.allow_messages_from,
                allow_messages_to=chat.allow_messages_to,
                created_by=user_created_chat,
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
                avatar_photo_url=chat_data[1],
            )
        )

    return ChatListResponse(chat_list=chat_list)


@router.post(path="/chat/create_group", response_model=CreateGroupChatResponse)
async def create_group_chat(
    group_chat_info: CreateGroupChatBody,
    session: Session = Depends(check_access_token),
):
    """
    Создаёт групповой чат с пользователями.
    Каждому пользователю, добавленному в чат, отправляется сообщение,
    что чат создан.
    Чат также может быть помечен как рабочий.
    """
    owner_user = await app_state.user_repo.get_by_id(id_=session.user_id)
    not_found_users = []
    user_first_names = owner_user.first_name
    for i, user_id in enumerate(group_chat_info.user_id_list):
        user = await app_state.user_repo.get_by_id(id_=user_id)
        if not user or user.id == owner_user.id:
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
        chat_id=chat.id, user_id=owner_user.id, role=UserChatRole.owner
    )

    message_create_model = MessageCreate(
        type=MessageTypeEnum.created_chat,
        chat_id=chat.id,
        sender_chat_id=chat.id,
    )
    await create_and_send_message(
        message_create=message_create_model,
        chat=chat,
        group_created_by=UserCreatedChat(
            id=owner_user.id, first_name=owner_user.first_name
        ),
    )

    chat_avatar = (
        app_state.media_repo.get_media_url(id_=chat.avatar_photo_id)
        if chat.avatar_photo_id
        else None
    )
    return CreateGroupChatResponse(
        created_chat_info=BaseChatInfo(
            id=chat.id,
            name=chat.name,
            is_work_chat=chat.is_work_chat,
            allow_messages_from=chat.allow_messages_from,
            allow_messages_to=chat.allow_messages_to,
            avatar_photo_url=chat_avatar,
        )
    )


@router.get(path="/chat/get_users", response_model=GetChatUsersResponse)
async def get_chat_users(
    chat_id: UUID4, session: Session = Depends(check_access_token)
):
    await is_group_chat_with_user_exists(chat_id=chat_id, session=session)

    chat_users = await app_state.chat_repo.get_chat_users_with_roles(
        chat_id=chat_id
    )
    current_user = list(
        filter(lambda user: user.id == session.user_id, chat_users)
    )[0]

    chat_users = [
        ChatUser(
            id=user.id,
            name=user.name,
            avatar_photo_url=(
                app_state.media_repo.get_media_url(id_=user.avatar_photo_id)
                if user.avatar_photo_id
                else None
            ),
            chat_role=user.role,
            last_online=user.last_online,
            can_exclude=current_user.id != user.id
            and (
                current_user.role == UserChatRole.owner
                or current_user.id == user.added_by_user
                and user.role == UserChatRole.member
                or current_user.role == UserChatRole.admin
                and user.role == UserChatRole.member
            ),
        )
        for user in chat_users
    ]

    return GetChatUsersResponse(users=chat_users)


@router.put(path="/chat/add_user")
async def add_user_to_chat(
        body: AddRemoveUserFromChatBody,
        session: Session = Depends(check_access_token),
):
    await is_group_chat_with_user_exists(chat_id=body.chat_id, session=session)

    user_to_add = await app_state.user_repo.get_by_id(id_=body.user_id)
    if not user_to_add:
        logger.error(
            "User not found. user_id=%s, session=%s",
            body.user_id,
            session.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatUserActionStatusEnum.user_not_found,
        )

    await app_state.chat_repo.add_chat_participant(
        chat_id=body.chat_id,
        user_id=user_to_add.id,
        added_by_user=session.user_id,
    )
