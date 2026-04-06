from fastapi import FastAPI, Request
from pathlib import Path
import json

app = FastAPI()

@app.post("/bitrix/install")
async def bitrix_install(request: Request):
    data = await request.json()
    Path("storage").mkdir(exist_ok=True)
    with open("storage/bitrix_install.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"status": "ok"}
