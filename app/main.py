import os
import time
import json
from pathlib import Path
from typing import Optional, Any

import requests
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="Bitrix24 ↔ Chat4 Bridge")

STORE_FILE = Path("store.json")

CHAT4_BASE_URL = os.getenv("CHAT4_BASE_URL", "https://app.chat4.tech")
CHAT4_CLIENT_ID = os.getenv("CHAT4_CLIENT_ID", "app.69b00b3342e7a8.01778095")
CHAT4_CLIENT_SECRET = os.getenv("CHAT4_CLIENT_SECRET", "J2CwZ8lW03neSguqkUnNBYdEgsjGRM5SatV7F3WtFaLCxCdU25")

BITRIX_WEBHOOK_BASE = os.getenv("BITRIX_WEBHOOK_BASE", "https://b24-nzzmi5.bitrix24.ru/rest/1/5r4bbqdvz4jstgoo/")
BITRIX_CONNECTOR = os.getenv("BITRIX_CONNECTOR", "my_site_chat")

TOKEN_CACHE = {
    "access_token": None,
    "expires_at": 0,
}


class ExternalIncomingMessage(BaseModel):
    session_id: str
    user_id: str
    text: str
    user_name: Optional[str] = None
    chat4_chat_id: Optional[str] = None


class Chat4SendBody(BaseModel):
    text: str


def load_store() -> dict:
    if STORE_FILE.exists():
        try:
            return json.loads(STORE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"sessions": {}, "messages": []}
    return {"sessions": {}, "messages": []}


def save_store(store: dict):
    STORE_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def log_message(
    direction: str,
    session_id: Optional[str],
    text: Optional[str],
    payload: Any = None,
    result: Any = None
):
    store = load_store()
    store["messages"].append({
        "ts": int(time.time()),
        "direction": direction,
        "session_id": session_id,
        "text": text,
        "payload": payload,
        "result": result,
    })
    save_store(store)


def ensure_session(
    session_id: str,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    chat4_chat_id: Optional[str] = None
):
    store = load_store()
    sessions = store["sessions"]

    if session_id not in sessions:
        sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "user_name": user_name,
            "chat4_chat_id": chat4_chat_id,
            "created_at": int(time.time())
        }
    else:
        if user_id:
            sessions[session_id]["user_id"] = user_id
        if user_name:
            sessions[session_id]["user_name"] = user_name
        if chat4_chat_id:
            sessions[session_id]["chat4_chat_id"] = chat4_chat_id

    save_store(store)
    return sessions[session_id]


def get_session(session_id: str) -> Optional[dict]:
    store = load_store()
    return store["sessions"].get(session_id)


def get_chat4_access_token() -> str:
    now = time.time()

    if TOKEN_CACHE["access_token"] and now < TOKEN_CACHE["expires_at"] - 30:
        return TOKEN_CACHE["access_token"]

    if not CHAT4_CLIENT_ID or not CHAT4_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="CHAT4_CLIENT_ID or CHAT4_CLIENT_SECRET is missing")

    resp = requests.post(
        f"{CHAT4_BASE_URL}/api/auth/token/",
        data={
            "grant_type": "client_credentials",
            "client_id": CHAT4_CLIENT_ID,
            "client_secret": CHAT4_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Chat4 token error: {resp.text}")

    data = resp.json()
    access_token = data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=500, detail=f"Chat4 token missing access_token: {data}")

    TOKEN_CACHE["access_token"] = access_token
    TOKEN_CACHE["expires_at"] = now + 3500
    return access_token


def chat4_request(method: str, path: str, json_body: Optional[dict] = None):
    token = get_chat4_access_token()

    resp = requests.request(
        method=method,
        url=f"{CHAT4_BASE_URL}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=json_body,
        timeout=30,
    )

    if resp.status_code == 401:
        TOKEN_CACHE["access_token"] = None
        TOKEN_CACHE["expires_at"] = 0
        token = get_chat4_access_token()

        resp = requests.request(
            method=method,
            url=f"{CHAT4_BASE_URL}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=json_body,
            timeout=30,
        )

    return resp


def chat4_get_messages(chat_id: str):
    resp = chat4_request("GET", f"/api/chats/chats/{chat_id}/messages/")
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Chat4 get messages failed: {resp.text}")
    return resp.json()


def chat4_send_message(chat_id: str, text: str):
    resp = chat4_request(
        "POST",
        f"/api/chats/chats/{chat_id}/send_message/",
        json_body={"text": text}
    )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Chat4 send failed: {resp.text}")
    return resp.json() if resp.text else {"ok": True}


def bitrix_send_message(external_user_id: str, external_chat_id: str, text: str, user_name: Optional[str] = None):
    if not BITRIX_WEBHOOK_BASE:
        raise HTTPException(status_code=500, detail="BITRIX_WEBHOOK_BASE is missing")

    payload = {
        "CONNECTOR": BITRIX_CONNECTOR,
        "LINE": 1,
        "MESSAGES": [
            {
                "user": {
                    "id": external_user_id,
                    "name": user_name or external_user_id
                },
                "message": {
                    "id": str(int(time.time() * 1000)),
                    "date": int(time.time()),
                    "text": text
                },
                "chat": {
                    "id": external_chat_id
                }
            }
        ]
    }

    resp = requests.post(
        f"{BITRIX_WEBHOOK_BASE}/imconnector.send.messages",
        json=payload,
        timeout=30,
    )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Bitrix send failed: {resp.text}")

    return resp.json() if resp.text else {"ok": True}


@app.get("/")
def root():
    return {"status": "ok", "service": "Bitrix24 ↔ Chat4 bridge"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/store")
def debug_store():
    return load_store()


@app.post("/chat4/token/test")
def chat4_token_test():
    token = get_chat4_access_token()
    return {
        "status": "ok",
        "access_token_preview": token[:20] + "..." if token else None
    }


@app.get("/chat4/messages/{chat_id}")
def chat4_messages(chat_id: str):
    result = chat4_get_messages(chat_id)
    return {"status": "ok", "chat_id": chat_id, "result": result}


@app.post("/chat4/send/{chat_id}")
def chat4_send(chat_id: str, body: Chat4SendBody):
    result = chat4_send_message(chat_id, body.text)
    log_message(
        direction="to_chat4_manual",
        session_id=None,
        text=body.text,
        payload={"chat_id": chat_id},
        result=result
    )
    return {"status": "ok", "chat_id": chat_id, "result": result}


@app.post("/external/incoming-message")
def external_incoming_message(data: ExternalIncomingMessage):
    session = ensure_session(
        session_id=data.session_id,
        user_id=data.user_id,
        user_name=data.user_name,
        chat4_chat_id=data.chat4_chat_id
    )

    bitrix_result = bitrix_send_message(
        external_user_id=data.user_id,
        external_chat_id=data.session_id,
        text=data.text,
        user_name=data.user_name
    )

    log_message(
        direction="external_to_bitrix",
        session_id=data.session_id,
        text=data.text,
        payload=data.model_dump(),
        result=bitrix_result
    )

    return {
        "status": "ok",
        "session": session,
        "bitrix_result": bitrix_result
    }


@app.post("/bitrix/events")
async def bitrix_events(request: Request):
    body = await request.json()

    log_message(
        direction="bitrix_webhook_raw",
        session_id=None,
        text=None,
        payload=body
    )

    session_id = None
    text = None

    if isinstance(body, dict):
        session_id = (
            body.get("session_id")
            or body.get("chat_id")
            or body.get("data", {}).get("PARAMS", {}).get("CHAT_ID")
            or body.get("data", {}).get("CHAT_ID")
        )

        text = (
            body.get("text")
            or body.get("message")
            or body.get("data", {}).get("PARAMS", {}).get("MESSAGE")
            or body.get("data", {}).get("MESSAGE")
        )

    if not session_id or not text:
        return {"status": "ignored", "reason": "session_id or text not found", "raw": body}

    session = get_session(session_id)

    if not session:
        return {"status": "ignored", "reason": f"unknown session_id: {session_id}"}

    chat4_chat_id = session.get("chat4_chat_id")
    if not chat4_chat_id:
        return {"status": "ignored", "reason": f"no chat4_chat_id for session_id: {session_id}"}

    chat4_result = chat4_send_message(chat4_chat_id, text)

    log_message(
        direction="bitrix_to_chat4",
        session_id=session_id,
        text=text,
        payload=body,
        result=chat4_result
    )

    return {
        "status": "ok",
        "session_id": session_id,
        "chat4_chat_id": chat4_chat_id,
        "chat4_result": chat4_result
    }


@app.get("/external/session/{session_id}")
def external_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    store = load_store()
    messages = [m for m in store["messages"] if m.get("session_id") == session_id]

    return {
        "status": "ok",
        "session": session,
        "messages": messages
    }
