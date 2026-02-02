from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from database.models.accounts import UserModel, UserProfileModel
from schemas.profiles import UserProfileResponseSchema, UserProfileCreateSchema
from security.http import get_token
from config.dependencies import get_jwt_auth_manager, get_s3_storage_client, get_settings
from security.interfaces import JWTAuthManagerInterface
from storages.interfaces import S3StorageInterface
from exceptions.security import TokenExpiredError
from exceptions.storage import S3FileUploadError
from validation.profile import validate_image

router = APIRouter()

@router.post("/users/{user_id}/profile/",
             response_model=UserProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_profile(
        user_id: int,
        profile_data: UserProfileCreateSchema = Depends(),
        avatar: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        token: str = Depends(get_token),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        storage_client: S3StorageInterface = Depends(get_s3_storage_client),
        settings=Depends(get_settings)
):
    image_content = await validate_image(avatar)
    if not profile_data.info or not profile_data.info.strip():
        raise HTTPException(status_code=422, detail="Info field cannot be empty.")

    try:
        payload = jwt_manager.decode_access_token(token)
        current_user_id = payload.get("user_id")
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

    target_user = await db.get(UserModel, user_id)
    if not target_user or not target_user.is_active:
        raise HTTPException(status_code=401, detail="Target user not found or not active.")

    current_user = await db.get(UserModel, current_user_id)
    if current_user_id != user_id and (not current_user or current_user.group_id != 3):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to edit this profile."
        )

    existing = await db.execute(select(UserProfileModel).filter_by(user_id=user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already has a profile.")

    avatar_key = f"avatars/{user_id}_avatar.jpg"
    try:
        await storage_client.upload_file(avatar_key, image_content)
    except S3FileUploadError:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload avatar. Please try again later."
        )

    new_profile = UserProfileModel(
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        info=profile_data.info,
        avatar=avatar_key,
        user_id=user_id
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    new_profile.avatar = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{avatar_key}"

    return new_profile
