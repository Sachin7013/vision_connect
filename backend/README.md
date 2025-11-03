# VisionConnect Backend 📹

WiFi IP Camera Onboarding System with QR Code & P2P Relay (Similar to CP Plus Ezykam+)

## 🚀 Features

- ✅ **User Authentication** (Register/Login with JWT)
- ✅ **QR Code Generation** for camera onboarding
- ✅ **Camera Activation** via QR scan
- ✅ **Device Management** (List/View/Delete cameras)
- ✅ **P2P Relay Infrastructure** (WebSocket)
- ✅ **Cloud Storage** of device-user mapping
- ✅ **RESTful API** with FastAPI
- ✅ **MongoDB** for data persistence

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── auth.py              # JWT authentication utilities
│   ├── db.py                # MongoDB connection
│   ├── models.py            # Pydantic models
│   ├── camera_routes.py     # Camera onboarding endpoints
│   ├── qr_utils.py          # QR code generation
│   └── signaling.py         # WebSocket P2P signaling
├── requirements.txt
├── .env                     # Environment variables
├── API_TESTING_GUIDE.md     # Complete API testing guide
├── CONCEPT_EXPLAINED.md     # Beginner's concept guide
└── README.md                # This file
```

## 🛠️ Installation

### Prerequisites:
- Python 3.8+
- MongoDB running locally or MongoDB Atlas account

### Steps:

1. **Clone and navigate:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Create `.env` file (or set environment variables):
   ```env
   MONGO_URI=mongodb://localhost:27017/vision_connect
   SECRET_KEY=your-secret-key-change-in-production
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Verify it's running:**
   ```bash
   curl http://localhost:8000/
   ```

## 📚 Documentation

### Quick Links:
- **API Testing Guide**: [`API_TESTING_GUIDE.md`](./API_TESTING_GUIDE.md) - Complete curl examples
- **Concept Explained**: [`CONCEPT_EXPLAINED.md`](./CONCEPT_EXPLAINED.md) - Beginner-friendly explanation
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints:

#### Authentication:
- `POST /api/register` - Create new user account
- `POST /api/login` - User login (returns JWT token)

#### Camera Management:
- `GET /api/camera/models` - Get available camera models
- `POST /api/camera/onboard` - Initiate camera onboarding (generates QR)
- `POST /api/camera/activate` - Camera self-activation (called by camera)
- `GET /api/camera/devices` - Get user's cameras
- `GET /api/camera/devices/{id}` - Get specific camera details
- `DELETE /api/camera/devices/{id}` - Remove camera
- `GET /api/camera/check-status/{token}` - Check device activation status

#### WebSocket:
- `WS /ws` - P2P signaling for video streaming

## 🧪 Quick Test

### 1. Register a user:
```bash
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### 2. Generate QR code for camera:
```bash
curl -X POST "http://localhost:8000/api/camera/onboard" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "camera_model": "CP_PLUS_WIFI_V2",
    "wifi_ssid": "MyWiFi",
    "wifi_password": "mypass",
    "device_name": "Living Room"
  }'
```

### 3. Simulate camera activation:
```bash
curl -X POST "http://localhost:8000/api/camera/activate" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "TOKEN_FROM_STEP_2",
    "device_uid": "CAM123456",
    "camera_model": "CP_PLUS_WIFI_V2",
    "local_ip": "192.168.1.100"
  }'
```

## 🔄 How It Works

### Camera Onboarding Flow:

```
1. User logs in → Gets JWT token
2. User initiates onboarding → Server generates QR code
3. User shows QR to camera → Camera scans it
4. Camera connects to WiFi → Uses credentials from QR
5. Camera activates itself → Calls /api/camera/activate
6. Server links camera to user → Device status: active
7. User sees camera in app → Can now stream video
```

### QR Code Contains:
```json
{
  "wifi_ssid": "MyHomeWiFi",
  "wifi_password": "password123",
  "server_url": "https://yourapp.onrender.com",
  "device_token": "unique-activation-token",
  "user_id": "owner-user-id",
  "camera_model": "CP_PLUS_WIFI_V2"
}
```

## 🌐 Deployment to Render

### Configuration:

1. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Command:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables:**
   - `MONGO_URI`: MongoDB Atlas connection string
   - `SECRET_KEY`: Strong random secret for JWT signing

4. **Important:**
   - Update `SERVER_URL` in `camera_routes.py` to your Render URL
   - Use MongoDB Atlas (cloud MongoDB) for production
   - Enable HTTPS (Render provides this automatically)

## 🗄️ Database Schema

### Users Collection:
```javascript
{
  _id: ObjectId,
  email: String,
  password: String (hashed),
  created_at: String (ISO date)
}
```

### Cameras Collection:
```javascript
{
  _id: ObjectId,
  device_name: String,
  camera_model: String,
  owner_id: String (references users._id),
  wifi_ssid: String,
  device_token: String (for activation),
  device_uid: String (camera hardware ID),
  status: String ("pending" | "active" | "offline"),
  local_ip: String,
  created_at: String (ISO date),
  activated_at: String (ISO date)
}
```

## 🔐 Security

- **Passwords**: Hashed using Werkzeug
- **JWT Tokens**: HS256 algorithm, 24-hour expiration
- **Device Tokens**: UUID4, one-time use
- **CORS**: Configure properly in production
- **HTTPS**: Use SSL certificate in production

## 🐛 Troubleshooting

### MongoDB connection fails:
```bash
# Check if MongoDB is running:
mongod --version

# Check connection string in .env
MONGO_URI=mongodb://localhost:27017/vision_connect
```

### Import errors:
```bash
# Make sure you're running from backend directory:
cd backend
uvicorn app.main:app --reload
```

### QR code not displaying:
The `qr_code` field returns base64 PNG. Display in HTML:
```html
<img src="data:image/png;base64,{base64_string}" />
```

## 📱 Frontend Integration

### React Example:
```javascript
// 1. Login
const response = await fetch('http://localhost:8000/api/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({email, password})
});
const {access_token} = await response.json();

// 2. Generate QR
const qrResponse = await fetch('http://localhost:8000/api/camera/onboard', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    camera_model: 'CP_PLUS_WIFI_V2',
    wifi_ssid: 'MyWiFi',
    wifi_password: 'mypass',
    device_name: 'Living Room'
  })
});
const {qr_code, device_token} = await qrResponse.json();

// 3. Display QR
<img src={qr_code} alt="Scan with camera" />

// 4. Poll for activation
setInterval(async () => {
  const status = await fetch(`/api/camera/check-status/${device_token}`);
  const {activated} = await status.json();
  if (activated) {
    alert('Camera activated!');
  }
}, 2000);
```

## 🎯 Next Steps

- [ ] Build mobile app (React Native/Flutter)
- [ ] Implement video streaming player
- [ ] Add motion detection
- [ ] Cloud recording (optional)
- [ ] Push notifications
- [ ] Camera sharing between users
- [ ] Two-way audio

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Please read the concept guide first to understand the architecture.

## 📞 Support

- Read [`CONCEPT_EXPLAINED.md`](./CONCEPT_EXPLAINED.md) for detailed explanations
- Check [`API_TESTING_GUIDE.md`](./API_TESTING_GUIDE.md) for API examples
- Open an issue for bugs or questions

---

Built with ❤️ using FastAPI, MongoDB, and QR Code magic 🎯
