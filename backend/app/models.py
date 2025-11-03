# models.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# ===== User Models =====
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserCreate):
    id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ===== Camera/Device Models =====
class CameraModel(BaseModel):
    """Available camera models"""
    model_id: str
    model_name: str
    manufacturer: str = "Generic"
    supports_qr: bool = True

class DeviceOnboardRequest(BaseModel):
    """Request to start device onboarding - generates QR code"""
    camera_model: str  # e.g., "CP_PLUS_WIFI_V2"
    wifi_ssid: str
    wifi_password: str
    device_name: Optional[str] = "My Camera"

class DeviceActivation(BaseModel):
    """Camera sends this after scanning QR to activate itself"""
    device_token: str
    device_uid: str  # Unique hardware ID from camera
    camera_model: str
    local_ip: Optional[str] = None

class DeviceCreate(BaseModel):
    uid: str
    model: Optional[str] = "Unknown"
    owner_id: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_token: Optional[str] = None  # short setup token

class DeviceInDB(BaseModel):
    """Camera stored in database"""
    device_id: str
    device_uid: Optional[str] = None  # Hardware UID (None until camera activates)
    device_name: str
    camera_model: str
    owner_id: str
    wifi_ssid: str
    device_token: str
    status: str  # "pending", "active", "offline"
    local_ip: Optional[str] = None
    created_at: str
    activated_at: Optional[str] = None

class DeviceListResponse(BaseModel):
    """List of user's cameras"""
    devices: List[DeviceInDB]
