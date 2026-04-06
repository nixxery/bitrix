from fastapi import FastAPI, Request
import json
from pathlib import Path

app = FastAPI()

@app.post("/bitrix/install")
async def bitrix_install(request: Request):
    form = await request.form()
    data = dict(form)

    Path("storage").mkdir(exist_ok=True)
    with open("storage/bitrix_install.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "installed", "received": data}
