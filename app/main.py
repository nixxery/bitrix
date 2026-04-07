from fastapi import FastAPI, Request
from pathlib import Path
import json
import time
from pydantic import BaseModel
from .bitrix_app_client import (
    test_methods,
    register_connector,
    activate_connector,
    send_test_message,
    send_message_to_bitrix,
)

class IncomingMessage(BaseModel):
    user_id: str = "site-user-1"
    chat_id: str = "site-chat-1"
    message_id: str = "site-msg-1"
    text: str = "Привет, это сообщение с сайта"
    user_name: str = "Иван"
    
app = FastAPI(title="Bitrix Bridge")


@app.get("/")
def root():
    return {"status": "ok"}


@app.api_route("/bitrix/install", methods=["GET", "POST"])
async def bitrix_install(request: Request):
    if request.method == "GET":
        return {"status": "alive"}

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    print("BITRIX INSTALL DATA:", data)

    Path("/tmp").mkdir(exist_ok=True)
    with open("/tmp/bitrix_install.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "status": "saved",
        "keys": list(data.keys())
    }


@app.get("/app/test_methods")
def app_test_methods():
    return test_methods()


@app.post("/app/register_connector")
def app_register_connector():
    return register_connector()


@app.post("/app/activate_connector")
def app_activate_connector():
    return activate_connector()


@app.post("/app/send_test_message")
def app_send_test_message():
    return send_test_message()


@app.post("/external/incoming-message")
def external_incoming_message(data: IncomingMessage):
    payload = data.model_dump()
    print("EXTERNAL INCOMING:", payload)

    result = send_message_to_bitrix(
        external_user_id=payload["user_id"],
        external_chat_id=payload["chat_id"],
        external_message_id=payload["message_id"],
        text=payload["text"],
        user_name=payload["user_name"],
    )

    print("BITRIX SEND RESULT:", result)

    Path("/tmp").mkdir(exist_ok=True)
    with open("/tmp/last_external_to_bitrix.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "incoming": payload,
                "bitrix_result": result,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return {"status": "ok", "bitrix_result": result}


@app.post("/bitrix/events")
async def bitrix_events(request: Request):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    print("BITRIX EVENT:", data)

    Path("/tmp").mkdir(exist_ok=True)
    with open("/tmp/bitrix_event.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "received"}
