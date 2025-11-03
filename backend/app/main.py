# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import db, auth, signaling, models
from .models import DeviceCreate, UserCreate
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from jose import jwt

app = FastAPI(title="VisionConnect Backend")

# CORS - allow your frontend origin (during dev you likely use file:// or http://localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- REST: simple user register/login ----------
@app.post("/api/register")
async def register(user: UserCreate):
    existing = await db.users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = generate_password_hash(user.password)
    user_doc = {"email": user.email, "password": hashed}
    res = await db.users_collection.insert_one(user_doc)
    user_id = str(res.inserted_id)
    return {"user_id": user_id, "email": user.email}

@app.post("/api/login")
async def login(user: UserCreate):
    doc = await db.users_collection.find_one({"email": user.email})
    if not doc or not check_password_hash(doc["password"], user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"user_id": str(doc["_id"]), "email": doc["email"]})
    return {"access_token": token, "token_type": "bearer"}

# ---------- REST: register a camera (called by the phone after scanning/generating QR) ----------
@app.post("/api/devices")
async def add_device(device: DeviceCreate, token: str = None):
    # token: optional JWT of logged-in user; in frontend include Authorization normally
    owner_id = device.owner_id
    if token:
        payload = auth.decode_access_token(token)
        if payload:
            owner_id = payload.get("user_id")
    # create device record including short token for camera QR onboarding (random)
    setup_token = str(uuid.uuid4())[:8]
    device_doc = {
        "uid": device.uid,
        "model": device.model,
        "owner_id": owner_id,
        "wifi_ssid": device.wifi_ssid,
        "setup_token": setup_token,
        "status": "created"
    }
    await db.devices_collection.insert_one(device_doc)
    return {"message": "device created", "setup_token": setup_token}

# ---------- REST: get device info ----------
@app.get("/api/devices/{uid}")
async def get_device(uid: str):
    doc = await db.devices_collection.find_one({"uid": uid})
    if not doc:
        raise HTTPException(status_code=404, detail="Device not found")
    doc["_id"] = str(doc["_id"])
    return doc

# ---------- WebSocket endpoint for signaling ----------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    # client must send initial registration message: {"type":"register", "role":"device"|"user", "uid": "<uid>" , "user_id": "<id>"}
    try:
        init_msg = await ws.receive_text()
        msg = json.loads(init_msg)
        role = msg.get("role")
        if role == "device":
            uid = msg.get("uid")
            await signaling.register_device(uid, ws)
            await ws.send_text(json.dumps({"type": "registered", "role": "device", "uid": uid}))
            # listen loop
            while True:
                data = await ws.receive_text()
                payload = json.loads(data)
                # forward messages to user if requested
                if payload.get("to") == "user" and payload.get("user_id"):
                    await signaling.forward_to_user(payload["user_id"], payload)
        elif role == "user":
            user_id = msg.get("user_id")
            await signaling.register_user(user_id, ws)
            await ws.send_text(json.dumps({"type": "registered", "role": "user", "user_id": user_id}))
            while True:
                data = await ws.receive_text()
                payload = json.loads(data)
                # If user wants to contact a device
                target_uid = payload.get("target_uid")
                if target_uid:
                    # forward payload to device
                    await signaling.forward_to_device(target_uid, payload)
    except WebSocketDisconnect:
        # cleanup: remove from maps
        try:
            if role == "device":
                await signaling.unregister_device(uid)
            elif role == "user":
                await signaling.unregister_user(user_id)
        except Exception:
            pass
    except Exception as e:
        print("WS error:", e)
        await ws.close()
