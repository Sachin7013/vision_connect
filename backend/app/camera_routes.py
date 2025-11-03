# camera_routes.py
"""
Camera onboarding and management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List
import uuid
from datetime import datetime
from bson import ObjectId

from . import db, auth, qr_utils
from .models import (
    DeviceOnboardRequest, 
    DeviceActivation, 
    DeviceInDB, 
    DeviceListResponse,
    CameraModel
)

router = APIRouter(prefix="/api/camera", tags=["camera"])

# Configuration - Get from environment variable or use default
import os
SERVER_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")

# ===== Helper Functions =====
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and verify user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract token from "Bearer <token>" format
        token = authorization.replace("Bearer ", "")
        payload = auth.decode_access_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authorization")

# ===== Camera Model Endpoints =====
@router.get("/models", response_model=List[CameraModel])
async def get_camera_models():
    """
    Get list of supported camera models
    User selects one before adding device
    """
    # In production, store this in database
    models = [
        {
            "model_id": "CP_PLUS_WIFI_V2",
            "model_name": "CP Plus WiFi Camera V2",
            "manufacturer": "CP Plus",
            "supports_qr": True
        },
        {
            "model_id": "HIKVISION_DS_2CD",
            "model_name": "Hikvision DS-2CD Series",
            "manufacturer": "Hikvision",
            "supports_qr": True
        },
        {
            "model_id": "GENERIC_ONVIF",
            "model_name": "Generic ONVIF Camera",
            "manufacturer": "Generic",
            "supports_qr": True
        }
    ]
    return models

# ===== Device Onboarding: Step 1 - Generate QR Code =====
@router.post("/onboard")
async def initiate_device_onboarding(
    request: DeviceOnboardRequest,
    user_data: dict = Depends(get_current_user)
):
    """
    STEP 1: User initiates device onboarding
    
    Flow:
    1. User enters WiFi credentials and selects camera model in app
    2. App calls this endpoint
    3. Server creates pending device record and generates QR code
    4. App displays QR code to user
    5. User shows QR code to camera
    
    Returns: QR code image (base64) and device_token for tracking
    """
    user_id = user_data.get("user_id")
    
    # Generate unique device token (camera will use this to activate)
    device_token = str(uuid.uuid4())
    
    # Create pending device record in database
    device_doc = {
        "device_name": request.device_name,
        "camera_model": request.camera_model,
        "owner_id": user_id,
        "wifi_ssid": request.wifi_ssid,
        "device_token": device_token,
        "status": "pending",  # Will change to "active" when camera activates
        "device_uid": None,   # Camera will provide this during activation
        "local_ip": None,
        "created_at": datetime.utcnow().isoformat(),
        "activated_at": None
    }
    
    result = await db.devices_collection.insert_one(device_doc)
    device_id = str(result.inserted_id)
    
    # Generate QR code data
    qr_data = qr_utils.generate_qr_data(
        wifi_ssid=request.wifi_ssid,
        wifi_password=request.wifi_password,
        server_url=SERVER_URL,
        device_token=device_token,
        user_id=user_id,
        camera_model=request.camera_model
    )
    
    # Create QR code image
    qr_image = qr_utils.create_qr_code_image(qr_data)
    
    return {
        "success": True,
        "message": "QR code generated. Please show to camera.",
        "device_id": device_id,
        "device_token": device_token,
        "qr_code": qr_image,  # Base64 image data
        "qr_data": qr_data,   # Raw data for debugging
        "status": "pending"
    }

# ===== Device Activation: Step 2 - Camera Activates =====
@router.post("/activate")
async def activate_device(request: DeviceActivation):
    """
    STEP 2: Camera activates itself after scanning QR code
    
    Flow:
    1. Camera scans QR code and extracts data
    2. Camera connects to WiFi using credentials from QR
    3. Camera calls this endpoint with device_token and its hardware UID
    4. Server updates device status to "active"
    
    This endpoint is called BY THE CAMERA, not the mobile app
    """
    # Find pending device by token
    device = await db.devices_collection.find_one({
        "device_token": request.device_token,
        "status": "pending"
    })
    
    if not device:
        raise HTTPException(
            status_code=404, 
            detail="Device token not found or already activated"
        )
    
    # Update device with camera's hardware UID and activate
    update_result = await db.devices_collection.update_one(
        {"_id": device["_id"]},
        {
            "$set": {
                "device_uid": request.device_uid,
                "status": "active",
                "local_ip": request.local_ip,
                "activated_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to activate device")
    
    return {
        "success": True,
        "message": "Device activated successfully",
        "device_id": str(device["_id"]),
        "status": "active"
    }

# ===== Device Management =====
@router.get("/devices", response_model=DeviceListResponse)
async def get_user_devices(user_data: dict = Depends(get_current_user)):
    """
    Get all devices owned by current user
    """
    user_id = user_data.get("user_id")
    
    # Find all devices for this user
    cursor = db.devices_collection.find({"owner_id": user_id})
    devices = await cursor.to_list(length=100)
    
    # Format response
    device_list = []
    for device in devices:
        device_list.append({
            "device_id": str(device["_id"]),
            "device_uid": device.get("device_uid", "N/A"),
            "device_name": device.get("device_name", "Unnamed Camera"),
            "camera_model": device.get("camera_model", "Unknown"),
            "owner_id": device["owner_id"],
            "wifi_ssid": device.get("wifi_ssid", "N/A"),
            "device_token": device["device_token"],
            "status": device.get("status", "unknown"),
            "local_ip": device.get("local_ip"),
            "created_at": device.get("created_at", ""),
            "activated_at": device.get("activated_at")
        })
    
    return {"devices": device_list}

@router.get("/devices/{device_id}")
async def get_device_details(
    device_id: str,
    user_data: dict = Depends(get_current_user)
):
    """
    Get details of a specific device
    """
    user_id = user_data.get("user_id")
    
    try:
        device = await db.devices_collection.find_one({
            "_id": ObjectId(device_id),
            "owner_id": user_id
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid device ID format")
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "device_id": str(device["_id"]),
        "device_uid": device.get("device_uid", "N/A"),
        "device_name": device.get("device_name", "Unnamed Camera"),
        "camera_model": device.get("camera_model", "Unknown"),
        "wifi_ssid": device.get("wifi_ssid", "N/A"),
        "status": device.get("status", "unknown"),
        "local_ip": device.get("local_ip"),
        "created_at": device.get("created_at", ""),
        "activated_at": device.get("activated_at")
    }

@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: str,
    user_data: dict = Depends(get_current_user)
):
    """
    Remove a device from user's account
    """
    user_id = user_data.get("user_id")
    
    try:
        result = await db.devices_collection.delete_one({
            "_id": ObjectId(device_id),
            "owner_id": user_id
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid device ID format")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "success": True,
        "message": "Device removed successfully"
    }

@router.get("/check-status/{device_token}")
async def check_device_status(device_token: str):
    """
    Check if device has been activated
    Mobile app can poll this while showing QR code
    """
    device = await db.devices_collection.find_one({"device_token": device_token})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "device_id": str(device["_id"]),
        "status": device.get("status", "unknown"),
        "device_name": device.get("device_name"),
        "activated": device.get("status") == "active"
    }
