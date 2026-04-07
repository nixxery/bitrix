from fastapi import FastAPI, Request
from pathlib import Path
import json

from .bitrix_app_client import (
    test_methods,
    register_connector,
    activate_connector,
    send_test_message
)
app = FastAPI()

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
        "keys": list(data.keys()),
        "data": data
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
