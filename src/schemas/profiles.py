from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date
from typing import Optional
from validation.profile import validate_name, validate_gender, validate_birth_date


class UserProfileCreateSchema(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def check_names(cls, v: str) -> str:
        return validate_name(v)

    @field_validator("gender")
    @classmethod
    def check_gender(cls, v: str) -> str:
        return validate_gender(v)

    @field_validator("date_of_birth")
    @classmethod
    def check_dob(cls, v: date) -> date:
        return validate_birth_date(v)


class UserProfileResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    first_name: str
    last_name: str
    avatar: Optional[str]
    gender: str
    date_of_birth: date
    info: Optional[str]
