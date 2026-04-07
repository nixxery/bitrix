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

def refresh_access_token() -> str:
    url = "https://oauth.bitrix.info/oauth/token/"
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    }

    resp = requests.post(url, data=data, timeout=20)
    print("REFRESH STATUS:", resp.status_code)
    print("REFRESH BODY:", resp.text)
    resp.raise_for_status()

    result = resp.json()

    global ACCESS_TOKEN, REFRESH_TOKEN
    ACCESS_TOKEN = result["access_token"]
    REFRESH_TOKEN = result["refresh_token"]

    print("NEW ACCESS TOKEN:", ACCESS_TOKEN)
    return ACCESS_TOKEN


def bitrix_app_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    global ACCESS_TOKEN

    url = f"{CLIENT_ENDPOINT}{method}"
    payload = dict(params)
    payload["auth"] = ACCESS_TOKEN

    resp = requests.post(url, json=payload, timeout=20)
    print("URL:", url)
    print("STATUS:", resp.status_code)
    print("BODY:", resp.text)

    if resp.status_code == 401:
        print("ACCESS TOKEN EXPIRED, TRYING REFRESH...")
        refresh_access_token()
        payload["auth"] = ACCESS_TOKEN
        resp = requests.post(url, json=payload, timeout=20)
        print("RETRY STATUS:", resp.status_code)
        print("RETRY BODY:", resp.text)

    resp.raise_for_status()
    return resp.json()


def test_methods() -> Dict[str, Any]:
    return bitrix_app_call("methods", {})


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


def send_test_message() -> Dict[str, Any]:
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
                    "text": "Привет из внешнего сервиса!"
                }
            }
        ]
    }
    return bitrix_app_call("imconnector.send.messages", params)
