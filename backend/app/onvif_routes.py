# onvif_routes.py
"""
API routes for ONVIF camera discovery and management
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from . import db, auth
from .onvif_utils import ONVIFCameraManager, discover_onvif_cameras, add_onvif_camera

router = APIRouter(prefix="/api/onvif", tags=["onvif"])


# ========== Request/Response Models ==========

class CameraDiscoveryResponse(BaseModel):
    """Response model for discovered cameras"""
    cameras: List[dict]
    count: int


class ONVIFCameraAdd(BaseModel):
    """Request model to add ONVIF camera"""
    camera_name: str
    ip: str
    port: int = 80
    username: str
    password: str


class ONVIFCameraTest(BaseModel):
    """Request model to test ONVIF camera connection"""
    ip: str
    port: int = 80
    username: str
    password: str


# ========== Helper Functions ==========

async def get_current_user(authorization: str = Depends(auth.decode_access_token)):
    """Extract user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    return authorization


# ========== API Endpoints ==========

@router.get("/discover", response_model=CameraDiscoveryResponse)
async def discover_cameras(timeout: int = 5):
    """
    Discover all ONVIF cameras on local network
    
    Similar to ONVIF Device Manager's "Refresh" button
    Uses WS-Discovery protocol to find cameras automatically
    
    Args:
        timeout: Discovery timeout in seconds (default: 5)
    
    Returns:
        List of discovered cameras with IP, name, manufacturer
    """
    try:
        cameras = discover_onvif_cameras(timeout)
        
        return {
            "cameras": cameras,
            "count": len(cameras)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.post("/test-connection")
async def test_camera_connection(request: ONVIFCameraTest):
    """
    Test connection to ONVIF camera without adding it
    
    Verifies:
    - IP is reachable
    - ONVIF port is accessible
    - Credentials are correct
    - Camera responds to ONVIF commands
    
    Returns:
        Camera information if connection successful
    """
    try:
        # Try to connect
        camera = ONVIFCameraManager.connect_camera(
            request.ip,
            request.port,
            request.username,
            request.password
        )
        
        if not camera:
            raise HTTPException(status_code=400, detail="Cannot connect to camera. Check IP, port, and credentials.")
        
        # Get camera info
        camera_info = ONVIFCameraManager.get_camera_info(camera)
        
        # Get RTSP URL
        rtsp_url = ONVIFCameraManager.get_rtsp_url(camera)
        
        return {
            "success": True,
            "message": "Connection successful",
            "camera_info": {
                "manufacturer": camera_info.get("manufacturer", "Unknown"),
                "model": camera_info.get("model", "Unknown"),
                "firmware": camera_info.get("firmware_version", ""),
                "serial": camera_info.get("serial_number", ""),
                "rtsp_url": rtsp_url
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@router.post("/add-camera")
async def add_camera(
    request: ONVIFCameraAdd,
    user_data: dict = Depends(get_current_user)
):
    """
    Add ONVIF camera to user's account
    
    Process:
    1. Connect to camera via ONVIF
    2. Get camera details (model, manufacturer, etc.)
    3. Get RTSP stream URLs
    4. Save to database linked to user
    
    Returns:
        Camera details and device ID
    """
    try:
        user_id = user_data.get("user_id")
        
        # Connect and get camera info
        camera_data = add_onvif_camera(
            request.ip,
            request.port,
            request.username,
            request.password
        )
        
        # Create device document for database
        device_doc = {
            "device_name": request.camera_name,
            "device_uid": camera_data.get("serial_number", f"ONVIF_{request.ip}"),
            "camera_model": camera_data.get("model", "Unknown"),
            "manufacturer": camera_data.get("manufacturer", "Unknown"),
            "owner_id": user_id,
            "camera_type": "onvif",
            
            # ONVIF specific fields
            "camera_ip": request.ip,
            "onvif_port": request.port,
            "onvif_username": request.username,
            "onvif_password": request.password,  # TODO: Encrypt this!
            
            # Stream URLs
            "rtsp_url_main": camera_data.get("rtsp_url_main"),
            "rtsp_url_sub": camera_data.get("rtsp_url_sub"),
            "snapshot_url": camera_data.get("snapshot_url"),
            
            # Capabilities
            "capabilities": camera_data.get("capabilities", {}),
            
            # Status
            "status": "active",
            "source": "onvif_manual",
            "created_at": datetime.utcnow().isoformat(),
            "activated_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        result = await db.devices_collection.insert_one(device_doc)
        device_id = str(result.inserted_id)
        
        return {
            "success": True,
            "message": f"Camera '{request.camera_name}' added successfully",
            "device_id": device_id,
            "camera_info": {
                "manufacturer": camera_data.get("manufacturer"),
                "model": camera_data.get("model"),
                "ip": request.ip,
                "rtsp_url": camera_data.get("rtsp_url_main"),
                "capabilities": camera_data.get("capabilities")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add camera: {str(e)}")


@router.get("/camera/{device_id}/stream-url")
async def get_camera_stream_url(
    device_id: str,
    user_data: dict = Depends(get_current_user)
):
    """
    Get RTSP stream URL for a camera
    
    Returns:
        Main and sub stream URLs
    """
    try:
        from bson import ObjectId
        
        user_id = user_data.get("user_id")
        
        # Find camera
        camera = await db.devices_collection.find_one({
            "_id": ObjectId(device_id),
            "owner_id": user_id
        })
        
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        return {
            "device_id": device_id,
            "device_name": camera.get("device_name"),
            "rtsp_url_main": camera.get("rtsp_url_main"),
            "rtsp_url_sub": camera.get("rtsp_url_sub"),
            "snapshot_url": camera.get("snapshot_url")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/camera/{device_id}/refresh")
async def refresh_camera_info(
    device_id: str,
    user_data: dict = Depends(get_current_user)
):
    """
    Refresh camera information and stream URLs
    
    Useful if camera IP changed or streams not working
    """
    try:
        from bson import ObjectId
        
        user_id = user_data.get("user_id")
        
        # Find camera
        camera = await db.devices_collection.find_one({
            "_id": ObjectId(device_id),
            "owner_id": user_id
        })
        
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Reconnect to camera
        camera_data = add_onvif_camera(
            camera.get("camera_ip"),
            camera.get("onvif_port", 80),
            camera.get("onvif_username"),
            camera.get("onvif_password")
        )
        
        # Update database
        await db.devices_collection.update_one(
            {"_id": ObjectId(device_id)},
            {"$set": {
                "rtsp_url_main": camera_data.get("rtsp_url_main"),
                "rtsp_url_sub": camera_data.get("rtsp_url_sub"),
                "snapshot_url": camera_data.get("snapshot_url"),
                "firmware_version": camera_data.get("firmware_version"),
                "updated_at": datetime.utcnow().isoformat()
            }}
        )
        
        return {
            "success": True,
            "message": "Camera information refreshed",
            "rtsp_url": camera_data.get("rtsp_url_main")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-brands")
async def get_supported_brands():
    """
    List of camera brands known to support ONVIF
    
    Educational endpoint for users
    """
    return {
        "brands": [
            {"name": "CP Plus", "onvif_support": "Yes (most models)", "default_port": 80},
            {"name": "Hikvision", "onvif_support": "Yes", "default_port": 80},
            {"name": "Dahua", "onvif_support": "Yes", "default_port": 80},
            {"name": "Axis", "onvif_support": "Yes", "default_port": 80},
            {"name": "Sony", "onvif_support": "Yes (select models)", "default_port": 80},
            {"name": "Panasonic", "onvif_support": "Yes", "default_port": 80},
            {"name": "Bosch", "onvif_support": "Yes", "default_port": 80},
            {"name": "Vivotek", "onvif_support": "Yes", "default_port": 80},
        ],
        "note": "Most modern IP cameras support ONVIF. Check camera documentation or try discovery."
    }
