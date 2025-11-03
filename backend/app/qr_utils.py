# qr_utils.py
"""
QR Code generation utility for camera onboarding
"""
import qrcode
import json
import base64
from io import BytesIO
from typing import Dict

def generate_qr_data(
    wifi_ssid: str,
    wifi_password: str,
    server_url: str,
    device_token: str,
    user_id: str,
    camera_model: str
) -> Dict:
    """
    Generate data structure to be encoded in QR code
    
    This data is what the camera will read and use to:
    1. Connect to WiFi network
    2. Register itself with your cloud server
    3. Link to the user who scanned the QR
    """
    qr_payload = {
        "wifi_ssid": wifi_ssid,
        "wifi_password": wifi_password,
        "server_url": server_url,
        "device_token": device_token,
        "user_id": user_id,
        "camera_model": camera_model,
        "version": "1.0"
    }
    return qr_payload

def create_qr_code_image(data: Dict, size: int = 10) -> str:
    """
    Generate QR code image from data dictionary
    Returns: Base64 encoded image string for easy transmission
    """
    # Convert dict to JSON string
    json_data = json.dumps(data)
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls size (1 is smallest)
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=size,
        border=4,
    )
    
    # Add data and generate
    qr.add_data(json_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for API response
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def create_qr_code_url(data: Dict, size: int = 10) -> str:
    """
    Alternative: Generate QR code and return as data URL
    Useful for mobile apps to display directly
    """
    return create_qr_code_image(data, size)
