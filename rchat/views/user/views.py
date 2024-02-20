from fastapi import APIRouter, Depends

import logging

from rchat.state import app_state
from rchat.views.auth.helpers import check_access_token
from rchat.repository.session import Session
from rchat.views.user.models import FindUsersResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/user/profile")
def get_profile_data(session: Session = Depends(check_access_token)):
    pass


@router.get("/user/find")
async def get_match_users(
        match_str: str,
        session: Session = Depends(check_access_token)
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
        match_str=match_str,
        # except_user_id=session.user_id
    )

    return FindUsersResponse(users=match_users)
