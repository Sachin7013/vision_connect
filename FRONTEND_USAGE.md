# Frontend Usage Guide

## 🎯 Quick Start

### 1. Make sure backend server is running:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Open the frontend:
Simply open `index.html` in your browser:
- **Option 1:** Double-click `index.html`
- **Option 2:** Right-click → Open with → Browser
- **Option 3:** Drag and drop into browser window

### 3. Test the complete flow:

#### **Step 1: Login** (Pre-filled for testing)
- Email: `test@you.com`
- Password: `secret`
- Click "Login"

*Note: This user already exists in your database*

#### **Step 2: View Dashboard**
- After login, you'll see "My Cameras" tab
- Currently shows your existing camera

#### **Step 3: Add New Camera**
1. Click "Add Camera" tab
2. Fill in the form:
   - **Camera Model:** Select "CP Plus WiFi Camera V2"
   - **Camera Name:** "Bedroom Camera"
   - **WiFi Network:** Your actual WiFi name
   - **WiFi Password:** Your actual WiFi password
3. Click "Generate QR Code"

#### **Step 4: QR Code Display**
- A QR code will be generated and displayed
- The app automatically polls every 2 seconds to check if camera activated
- Show this QR to your camera (or simulate activation)

#### **Step 5: Simulate Camera Activation**
Open a new terminal and run:
```bash
curl -X POST "http://localhost:8000/api/camera/activate" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "COPY_TOKEN_FROM_BROWSER_CONSOLE",
    "device_uid": "CAM-TEST-12345",
    "camera_model": "CP_PLUS_WIFI_V2",
    "local_ip": "192.168.1.100"
  }'
```

*Note: Check browser console (F12) to see the device_token logged*

#### **Step 6: Success!**
- After activation, you'll see "✅ Camera activated successfully!"
- Automatically redirected to "My Cameras" tab
- Your new camera will appear in the list

---

## 🎨 Features Included

### Authentication:
- ✅ User registration with validation
- ✅ User login with JWT token
- ✅ Session persistence (localStorage)
- ✅ Logout functionality

### Camera Management:
- ✅ View all registered cameras
- ✅ Camera status badges (Active/Pending/Offline)
- ✅ Display camera details (Model, UID, WiFi, IP)
- ✅ Empty state when no cameras

### Camera Onboarding:
- ✅ Select from available camera models
- ✅ Enter WiFi credentials
- ✅ Generate QR code (Base64 PNG)
- ✅ Real-time status polling
- ✅ Auto-redirect after activation
- ✅ Cancel onboarding option

### UI/UX:
- ✅ Modern gradient design
- ✅ Responsive layout
- ✅ Loading spinners
- ✅ Alert messages (success/error/info)
- ✅ Tab-based navigation
- ✅ Smooth animations
- ✅ Form validation

---

## 🔧 Customization

### Change API URL:
Edit line 399 in `index.html`:
```javascript
const API_BASE_URL = 'https://your-render-app.onrender.com';
```

### Change Colors:
Edit the CSS gradient on line 16:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

---

## 📱 Mobile Testing

The app is responsive! Test on mobile:
1. Get your local IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Update API_BASE_URL to your local IP: `http://192.168.1.X:8000`
3. Open `index.html` on your phone's browser

---

## 🐛 Troubleshooting

### "Connection error. Is the server running?"
- Make sure backend is running on port 8000
- Check console (F12) for CORS errors
- Verify MongoDB is running

### QR code not displaying
- Check browser console for errors
- Verify JWT token is valid (might have expired)
- Try logging out and logging in again

### Camera activation not working
- Check the device_token in browser console
- Verify the curl command has correct token
- Check backend terminal for errors

### "Failed to load cameras"
- JWT token might be expired (24 hour validity)
- Try logout and login again
- Check backend logs

---

## 🎯 Testing Complete Flow (Quick)

1. **Open `index.html` in browser**
2. **Click Login** (credentials pre-filled)
3. **See existing camera** in "My Cameras" tab
4. **Click "Add Camera" tab**
5. **Fill form and generate QR**
6. **Open browser console (F12)**
7. **Copy the device_token from console logs**
8. **Open terminal and activate camera:**
   ```bash
   curl -X POST "http://localhost:8000/api/camera/activate" \
     -H "Content-Type: application/json" \
     -d '{"device_token":"PASTE_TOKEN_HERE","device_uid":"CAM999","camera_model":"CP_PLUS_WIFI_V2","local_ip":"192.168.1.99"}'
   ```
9. **Watch the QR screen automatically update to "✅ Camera activated!"**
10. **See new camera in "My Cameras" list**

---

## 📊 Browser Console Logs

The app logs useful information to console:
- API request/response data
- Device tokens
- Error messages
- Status check polling

Press **F12** → **Console** tab to see logs

---

## ✅ What's Working

- [x] User authentication (login/register)
- [x] JWT token management
- [x] Camera model listing
- [x] QR code generation (Base64 PNG)
- [x] Status polling every 2 seconds
- [x] Camera list display
- [x] Logout functionality
- [x] Form validation
- [x] Error handling
- [x] Responsive design

---

## 🚀 Production Deployment

When deploying to production:

1. **Update API URL** in `index.html`:
   ```javascript
   const API_BASE_URL = 'https://yourapp.onrender.com';
   ```

2. **Host frontend:**
   - **Option 1:** Netlify (drag & drop `index.html`)
   - **Option 2:** Vercel (git deploy)
   - **Option 3:** GitHub Pages
   - **Option 4:** Serve from FastAPI (add static files)

3. **Update CORS** in backend to allow your frontend domain

---

## 🎉 Success!

You now have a fully functional camera onboarding system! The frontend beautifully demonstrates:

- User authentication flow
- Camera onboarding with QR codes
- Real-time status updates
- Professional UI/UX

**Next steps:** Deploy to production and test with actual camera hardware!
