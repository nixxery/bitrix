from fastapi import FastAPI, Request
from pathlib import Path
import json

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

    Path("storage").mkdir(exist_ok=True)
    with open("storage/bitrix_install.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "saved"}
