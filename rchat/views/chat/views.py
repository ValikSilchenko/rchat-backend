from fastapi import APIRouter, Depends

from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.chat.helpers import get_chat_name
from rchat.views.chat.models import (
    ChatListItem,
    ChatListResponse,
    LastChatMessage,
)
from rchat.views.message.helpers import get_message_sender

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
