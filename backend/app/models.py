# models.py
from pydantic import BaseModel, Field
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str

class UserInDB(UserCreate):
    id: Optional[str]

class DeviceCreate(BaseModel):
    uid: str
    model: Optional[str] = "Unknown"
    owner_id: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_token: Optional[str] = None  # short setup token
