# VisionConnect API Testing Guide

## 🚀 Complete Camera Onboarding Flow

This guide walks you through the complete process of:
1. User registration/login
2. Initiating camera onboarding (generating QR code)
3. Camera activation
4. Viewing registered cameras

---

## Prerequisites

1. **Install dependencies:**
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```

2. **Ensure MongoDB is running:**
   - Check MongoDB Compass connection: `localhost:27017`

3. **Start the server:**
   ```powershell
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

4. **Verify server is running:**
   ```bash
   curl http://localhost:8000/
   ```
   Should return: `{"status":"online","service":"VisionConnect Backend"}`

---

## 📱 Step-by-Step Testing

### **Step 1: User Registration**

```bash
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "mypassword123"
  }'
```

**Expected Response:**
```json
{
  "user_id": "673f4a1b2c3d4e5f6a7b8c9d",
  "email": "user@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the `access_token` and `user_id`** - you'll need them!

---

### **Step 2: User Login** (if already registered)

```bash
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "mypassword123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "673f4a1b2c3d4e5f6a7b8c9d",
  "email": "user@example.com"
}
```

---

### **Step 3: Get Available Camera Models**

```bash
curl -X GET "http://localhost:8000/api/camera/models"
```

**Expected Response:**
```json
[
  {
    "model_id": "CP_PLUS_WIFI_V2",
    "model_name": "CP Plus WiFi Camera V2",
    "manufacturer": "CP Plus",
    "supports_qr": true
  },
  {
    "model_id": "HIKVISION_DS_2CD",
    "model_name": "Hikvision DS-2CD Series",
    "manufacturer": "Hikvision",
    "supports_qr": true
  }
]
```

---

### **Step 4: Initiate Camera Onboarding (Generate QR Code)**

**Replace `YOUR_ACCESS_TOKEN` with the token from Step 1/2**

```bash
curl -X POST "http://localhost:8000/api/camera/onboard" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "camera_model": "CP_PLUS_WIFI_V2",
    "wifi_ssid": "MyHomeWiFi",
    "wifi_password": "wifi_password_123",
    "device_name": "Living Room Camera"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "QR code generated. Please show to camera.",
  "device_id": "673f5b2c3d4e5f6a7b8c9daa",
  "device_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "qr_data": {
    "wifi_ssid": "MyHomeWiFi",
    "wifi_password": "wifi_password_123",
    "server_url": "https://yourapp.onrender.com",
    "device_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_id": "673f4a1b2c3d4e5f6a7b8c9d",
    "camera_model": "CP_PLUS_WIFI_V2",
    "version": "1.0"
  },
  "status": "pending"
}
```

**Important:**
- The `qr_code` field contains a base64-encoded PNG image
- You can display this in a mobile app or web browser
- **Save the `device_token`** - you'll use it to simulate camera activation

---

### **Step 5: Simulate Camera Activation**

**In real scenario, the camera does this automatically after scanning QR**

For testing, we'll simulate the camera calling the activation endpoint:

```bash
curl -X POST "http://localhost:8000/api/camera/activate" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "device_uid": "CAM123456789ABC",
    "camera_model": "CP_PLUS_WIFI_V2",
    "local_ip": "192.168.1.150"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Device activated successfully",
  "device_id": "673f5b2c3d4e5f6a7b8c9daa",
  "status": "active"
}
```

---

### **Step 6: Check Device Status** (Optional polling)

Mobile app can poll this while showing QR code to detect when camera activates:

```bash
curl -X GET "http://localhost:8000/api/camera/check-status/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Expected Response:**
```json
{
  "device_id": "673f5b2c3d4e5f6a7b8c9daa",
  "status": "active",
  "device_name": "Living Room Camera",
  "activated": true
}
```

---

### **Step 7: Get All User's Devices**

```bash
curl -X GET "http://localhost:8000/api/camera/devices" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "devices": [
    {
      "device_id": "673f5b2c3d4e5f6a7b8c9daa",
      "device_uid": "CAM123456789ABC",
      "device_name": "Living Room Camera",
      "camera_model": "CP_PLUS_WIFI_V2",
      "owner_id": "673f4a1b2c3d4e5f6a7b8c9d",
      "wifi_ssid": "MyHomeWiFi",
      "device_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "active",
      "local_ip": "192.168.1.150",
      "created_at": "2024-11-03T05:45:00.123456",
      "activated_at": "2024-11-03T05:46:15.654321"
    }
  ]
}
```

---

### **Step 8: Get Specific Device Details**

```bash
curl -X GET "http://localhost:8000/api/camera/devices/673f5b2c3d4e5f6a7b8c9daa" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### **Step 9: Delete Device**

```bash
curl -X DELETE "http://localhost:8000/api/camera/devices/673f5b2c3d4e5f6a7b8c9daa" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Device removed successfully"
}
```

---

## 🔧 Testing with Postman

1. Import the following as a Postman collection
2. Create an environment variable `access_token`
3. Use `{{access_token}}` in Authorization headers

### Environment Variables:
- `base_url`: `http://localhost:8000`
- `access_token`: (set after login)
- `device_token`: (set after onboarding)

---

## 🌐 Interactive API Documentation

FastAPI provides automatic interactive docs:

1. **Swagger UI**: http://localhost:8000/docs
2. **ReDoc**: http://localhost:8000/redoc

You can test all endpoints directly from the browser!

---

## 🐛 Troubleshooting

### Error: "Authorization header missing"
- Make sure to include: `-H "Authorization: Bearer YOUR_ACCESS_TOKEN"`

### Error: "Invalid token"
- Token may have expired (24 hours validity)
- Generate new token by logging in again

### Error: "Device token not found"
- Device may already be activated
- Check device status first

### QR Code not displaying
- The `qr_code` field is base64 encoded
- Use an HTML img tag: `<img src="{qr_code}" />`
- Or decode and save as PNG file

---

## 📊 Database Verification

Check MongoDB Compass:

1. **Database**: `vision_connect`
2. **Collections**:
   - `user`: Contains registered users
   - `camera`: Contains device records

### Sample Camera Document:
```json
{
  "_id": ObjectId("673f5b2c3d4e5f6a7b8c9daa"),
  "device_name": "Living Room Camera",
  "camera_model": "CP_PLUS_WIFI_V2",
  "owner_id": "673f4a1b2c3d4e5f6a7b8c9d",
  "wifi_ssid": "MyHomeWiFi",
  "device_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "active",
  "device_uid": "CAM123456789ABC",
  "local_ip": "192.168.1.150",
  "created_at": "2024-11-03T05:45:00.123456",
  "activated_at": "2024-11-03T05:46:15.654321"
}
```

---

## 🚀 Deployment to Render

### Before deploying:

1. **Update SERVER_URL in `camera_routes.py`:**
   ```python
   SERVER_URL = "https://your-app-name.onrender.com"
   ```

2. **Add environment variables on Render:**
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `SECRET_KEY`: Strong random secret for JWT

3. **Build command:** `pip install -r requirements.txt`

4. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## 📱 Next Steps: Mobile App Integration

### What the mobile app needs to do:

1. **Login screen**: Call `/api/login`
2. **Add Camera screen**:
   - Get camera models: `/api/camera/models`
   - User inputs WiFi credentials
   - Call `/api/camera/onboard`
   - Display the QR code image from response
   - Poll `/api/camera/check-status/{token}` every 2 seconds
   - When status becomes "active", show success message

3. **Camera list screen**:
   - Call `/api/camera/devices` to show all cameras
   - Each camera card shows name, model, status

4. **Live stream**: 
   - Connect via WebSocket to `/ws` (already implemented)
   - P2P relay for video streaming

---

## 🎯 How QR Code Works - Technical Explanation

### QR Code Contains:
```json
{
  "wifi_ssid": "MyHomeWiFi",
  "wifi_password": "password",
  "server_url": "https://yourapp.onrender.com",
  "device_token": "unique-token",
  "user_id": "user-id",
  "camera_model": "CP_PLUS_WIFI_V2"
}
```

### Camera Firmware Flow:
1. Camera enters setup mode (usually with a button press)
2. Camera activates its QR scanner (using camera lens)
3. Scans QR code and parses JSON data
4. Connects to WiFi using `wifi_ssid` and `wifi_password`
5. Makes HTTP POST to `{server_url}/api/camera/activate`
6. Sends `device_token` and its hardware `device_uid`
7. Server verifies token and activates device
8. Camera is now linked to user's account

### P2P Relay:
- Camera maintains WebSocket connection to server
- User app maintains WebSocket connection to server
- When user wants video: App → Server → Camera
- Video streams: Camera → Server → App
- Server just relays data (doesn't store video)

---

## ✅ Success!

You now have a complete WiFi IP camera onboarding system similar to Ezykam+!

**Features implemented:**
✅ User authentication (register/login)
✅ QR code generation for camera setup
✅ Camera activation via QR scan
✅ Device management (list/view/delete)
✅ P2P relay infrastructure (WebSocket)
✅ Cloud storage of device-user mapping

**Ready for production on Render.com!**
