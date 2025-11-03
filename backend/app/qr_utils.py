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
    camera_model: str,
    compact: bool = True
) -> Dict:
    """
    Generate data structure to be encoded in QR code
    
    This data is what the camera will read and use to:
    1. Connect to WiFi network
    2. Register itself with your cloud server
    3. Link to the user who scanned the QR
    
    Args:
        compact: If True, uses short keys (like Ezykam+) for smaller QR code
                 If False, uses descriptive keys (easier to debug)
    
    Format (compact=True) - Similar to CP Plus Ezykam+:
        {
            "s": "WiFi_Name",      // SSID
            "p": "password123",    // Password
            "t": "device_token",   // Token
            "u": "server_url",     // URL
            "m": "camera_model",   // Model
            "i": "user_id",        // User ID
            "v": 1                 // Version
        }
    """
    if compact:
        # Compact format (like Ezykam+) - smaller QR code
        qr_payload = {
            "s": wifi_ssid,         # SSID
            "p": wifi_password,     # Password
            "t": device_token,      # Token
            # "u": server_url,        # URL
            # "m": camera_model,      # Model
            # "i": user_id,           # User ID
            "v": 1                  # Version (integer)
        }
    else:
        # Descriptive format - easier to debug
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

def decode_qr_data(qr_data: Dict) -> Dict:
    """
    Decode QR data from compact format to full format
    Camera scans compact QR, server converts to readable format
    
    Args:
        qr_data: Dictionary from scanned QR code
    
    Returns:
        Dictionary with full descriptive keys
    
    Example:
        Input:  {"s": "MyWiFi", "p": "pass123", "t": "token", ...}
        Output: {"wifi_ssid": "MyWiFi", "wifi_password": "pass123", ...}
    """
    # Check if it's already in compact format
    if "s" in qr_data:
        # Compact format - decode it
        return {
            "wifi_ssid": qr_data.get("s"),
            "wifi_password": qr_data.get("p"),
            "device_token": qr_data.get("t"),
            "server_url": qr_data.get("u"),
            "camera_model": qr_data.get("m"),
            "user_id": qr_data.get("i"),
            "version": qr_data.get("v", 1)
        }
    else:
        # Already in full format
        return qr_data
