# signaling.py
from typing import Dict, Optional
import asyncio
import json
from fastapi import WebSocket

# Simple in-memory maps (single-process prototype)
devices: Dict[str, WebSocket] = {}     # camera uid -> websocket
users: Dict[str, WebSocket] = {}       # user_id -> websocket

async def register_device(uid: str, ws: WebSocket):
    devices[uid] = ws

async def unregister_device(uid: str):
    devices.pop(uid, None)

async def register_user(user_id: str, ws: WebSocket):
    users[user_id] = ws

async def unregister_user(user_id: str):
    users.pop(user_id, None)

async def forward_to_device(uid: str, message: dict):
    ws = devices.get(uid)
    if ws:
        await ws.send_text(json.dumps(message))

async def forward_to_user(user_id: str, message: dict):
    ws = users.get(user_id)
    if ws:
        await ws.send_text(json.dumps(message))
