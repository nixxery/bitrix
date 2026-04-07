from fastapi import FastAPI, Request
from pathlib import Path
import json
import time

from .bitrix_app_client import (
    test_methods,
    register_connector,
    activate_connector,
    send_test_message,
    send_message_to_bitrix,
)

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
async def external_incoming_message(request: Request):
    data = await request.json()
    print("EXTERNAL INCOMING:", data)

    external_user_id = str(data.get("user_id", "ext-user-1"))
    external_chat_id = str(data.get("chat_id", "ext-chat-1"))
    external_message_id = str(data.get("message_id", f"msg-{int(time.time())}"))
    text = str(data.get("text", "Пустое сообщение"))
    user_name = str(data.get("user_name", "Клиент"))

    result = send_message_to_bitrix(
        external_user_id=external_user_id,
        external_chat_id=external_chat_id,
        external_message_id=external_message_id,
        text=text,
        user_name=user_name,
    )

    print("BITRIX SEND RESULT:", result)

    Path("/tmp").mkdir(exist_ok=True)
    with open("/tmp/last_external_to_bitrix.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "incoming": data,
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
