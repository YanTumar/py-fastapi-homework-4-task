from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from database import get_db
from database.models.accounts import UserModel, UserProfileModel
from schemas.profiles import UserProfileResponseSchema
from security.http import get_token
from config.dependencies import get_jwt_auth_manager, get_s3_storage_client, get_settings
from security.interfaces import JWTAuthManagerInterface
from storages.interfaces import S3StorageInterface
from validation.profile import validate_name, validate_gender, validate_birth_date, validate_image

router = APIRouter()


@router.post("/users/{user_id}/profile/",
             response_model=UserProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_profile(
        user_id: int,
        first_name: str = Form(...),
        last_name: str = Form(...),
        gender: str = Form(...),
        date_of_birth: date = Form(...),
        info: str = Form(...),
        avatar: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        token: str = Depends(get_token),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        storage_client: S3StorageInterface = Depends(get_s3_storage_client),
        settings=Depends(get_settings)
):
    f_name = validate_name(first_name)
    l_name = validate_name(last_name)
    valid_gender = validate_gender(gender)
    valid_dob = validate_birth_date(date_of_birth)
    image_content = await validate_image(avatar)
    payload = jwt_manager.decode_access_token(token)
    current_user_id = payload.get("user_id")
    current_user = await db.get(UserModel, current_user_id)

    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="User not found or not active.")

    target_user = await db.get(UserModel, user_id)
    if not target_user or not target_user.is_active:
        raise HTTPException(status_code=404, detail="Target user not found or not active.")

    if current_user_id != user_id and current_user.group_id != 3:
        raise HTTPException(status_code=403, detail="You don't have permission.")

    existing = await db.execute(select(UserProfileModel).filter_by(user_id=user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already has a profile.")

    avatar_key = f"avatars/{user_id}_avatar.jpg"
    await storage_client.upload_file(avatar_key, image_content)
    new_profile = UserProfileModel(
        first_name=f_name, last_name=l_name, gender=valid_gender,
        date_of_birth=valid_dob, info=info, avatar=avatar_key, user_id=user_id
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    full_avatar_url = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{avatar_key}"
    new_profile.avatar = full_avatar_url

    return new_profile
