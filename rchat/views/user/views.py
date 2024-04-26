import logging

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from rchat.schemas.media import MediaTypeEnum
from rchat.schemas.session import Session
from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.views.user.models import (
    FindUsersResponse,
    FoundUser,
    ProfileResponse,
    ProfileUpdateBody,
    ProfileUpdateStatusEnum,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["User"])


@router.get(path="/user/profile", response_model=ProfileResponse)
async def get_profile_data(session: Session = Depends(check_access_token)):
    """
    Получает информацию о пользователе.
    """
    user = await app_state.user_repo.get_by_id(id_=session.user_id)

    return ProfileResponse(
        **user.model_dump(),
        avatar_photo_url=(
            app_state.media_repo.get_media_url(id_=user.avatar_photo_id)
            if user.avatar_photo_id
            else None
        ),
    )


@router.put(path="/user/update_profile")
async def update_profile_data(
    profile_data: ProfileUpdateBody,
    session: Session = Depends(check_access_token),
):
    """
    Обновляет данные пользователя.
    Если изменяется public_id, то проверяется, что он не занят.
    """
    user_exist = await app_state.user_repo.get_by_public_id(
        public_id=profile_data.public_id
    )
    if user_exist and user_exist.id != session.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ProfileUpdateStatusEnum.public_id_already_taken,
        )
    if profile_data.avatar_photo_id:
        photo = await app_state.media_repo.get_media_by_id(
            id_=profile_data.avatar_photo_id
        )
        if not photo or photo.type != MediaTypeEnum.photo:
            logger.error(
                "Photo does not exist or media is not a photo."
                " media_id=%s, media_found=%s",
                profile_data.avatar_photo_id,
                photo,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ProfileUpdateStatusEnum.invalid_photo_id,
            )

    await app_state.user_repo.update_user_info(
        user_id=session.user_id, **profile_data.model_dump()
    )


@router.get("/user/find", response_model=FindUsersResponse)
async def get_match_users(
    match_str: str, session: Session = Depends(check_access_token)
):
    """
    Метод поиска пользователей по public_id.

    Метод убирает из поисковой строки пробелы в начале и в конце,
    также убирает символ '@' из начала,
    если он есть, после чего выполняет поиск.
    """
    match_str = match_str.strip()
    if match_str.startswith("@"):
        match_str = match_str.lstrip("@")

    match_users = await app_state.user_repo.find_users_by_public_id(
        match_str=match_str, except_user_id=session.user_id
    )
    match_users = list(
        map(
            lambda user: FoundUser(
                id=user.id,
                public_id=user.public_id,
                name=(
                    f"{user.first_name} {user.last_name}"
                    if user.last_name
                    else user.first_name
                ),
                avatar_url=(
                    app_state.media_repo.get_media_url(
                        id_=user.avatar_photo_id
                    )
                    if user.avatar_photo_id
                    else None
                ),
            ),
            match_users,
        )
    )

    return FindUsersResponse(users=match_users)
