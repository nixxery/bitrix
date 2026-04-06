# app/bitrix_app_client.py
import requests
from typing import Dict, Any
import json
from pathlib import Path

# Данные из твоего bitrix_install.json
DOMAIN = "b24-nzzmi5.bitrix24.ru"
MEMBER_ID = "2ec7e1e767b504067b5f237e988c2406"
ACCESS_TOKEN = "c248d469008323000082458e000000010000073597a1deae70f33575c348f135f2b6f0"
REFRESH_TOKEN = "b2c7fb69008323000082458e00000001000007768b3c7c557b9f865938c4350a7d0679"
LINE_ID = 1
CONNECTOR_CODE = "my_site_chat"

def bitrix_app_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Вызов Bitrix24 REST через OAuth токен приложения."""
    url = f"https://{DOMAIN}/rest/{MEMBER_ID}/{ACCESS_TOKEN}/{method}"
    resp = requests.post(url, json=params, timeout=20)
    if resp.status_code != 200:
        print(f"ERROR {resp.status_code}:", resp.text)
    resp.raise_for_status()
    return resp.json()

def register_connector() -> Dict[str, Any]:
    params = {
        "CODE": CONNECTOR_CODE,
        "NAME": "My Site Chat",
    }
    return bitrix_app_call("imconnector.register", params)

def activate_connector() -> Dict[str, Any]:
    params = {
        "CONNECTOR": CONNECTOR_CODE,
        "LINE": LINE_ID,
        "ACTIVE": "Y",
    }
    return bitrix_app_call("imconnector.activate", params)

def send_test_message_to_bitrix() -> Dict[str, Any]:
    params = {
        "CONNECTOR": CONNECTOR_CODE,
        "LINE": LINE_ID,
        "MESSAGES": [
            {
                "user": {
                    "id": "external-user-1",
                    "name": "Тестовый клиент",
                },
                "chat": {
                    "id": "external-chat-1",
                    "name": "Чат с сайта",
                },
                "message": {
                    "id": "msg-1",
                    "text": "Привет из внешнего сервиса через FastAPI!"
                }
            }
        ]
    }
    return bitrix_app_call("imconnector.send.messages", params)
