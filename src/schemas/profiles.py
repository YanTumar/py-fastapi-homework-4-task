from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


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
