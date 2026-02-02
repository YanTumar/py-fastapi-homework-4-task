import re
from datetime import date
from fastapi import HTTPException, status, UploadFile


def validate_name(name: str):
    if not re.match(r"^[a-zA-Z]+$", name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{name} contains non-english letters"
        )
    return name.lower()


def validate_gender(gender: str):
    if gender not in ["man", "woman"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Gender must be one of 'man', 'woman'."
        )
    return gender


def validate_birth_date(birth_date: date):
    if birth_date.year <= 1900:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid birth date - year must be greater than 1900."
        )

    # Точний розрахунок віку
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    if age < 18:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="You must be at least 18 years old to register."
        )
    return birth_date


async def validate_image(avatar: UploadFile):
    if avatar.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid image format."
        )
    content = await avatar.read()
    if len(content) > 1 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image size exceeds 1 MB."
        )
    await avatar.seek(0)
    return content
