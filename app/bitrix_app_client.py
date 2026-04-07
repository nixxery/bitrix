import requests
from typing import Dict, Any

CLIENT_ENDPOINT = "https://b24-nzzmi5.bitrix24.ru/rest/"
ACCESS_TOKEN = "c248d469008323000082458e000000010000073597a1deae70f33575c348f135f2b6f0"
REFRESH_TOKEN = "b2c7fb69008323000082458e00000001000007768b3c7c557b9f865938c4350a7d0679"

# СЮДА ВСТАВЬ СВОИ НАСТОЯЩИЕ ДАННЫЕ
CLIENT_ID = "local.69d4326d55b427.59427213"
CLIENT_SECRET = "gCGC2KgmFuUpnkUbR2w442Sg5twfYxJBxpRfR9G0YGMe1Xeajz"

LINE_ID = 1
CONNECTOR_CODE = "my_site_chat"


def refresh_access_token() -> str:
    global ACCESS_TOKEN
    global REFRESH_TOKEN

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
        "ID": "my_site_chat",
        "NAME": "My Site Chat",
        "ICON": {
            "DATA_IMAGE": "data:image/svg+xml,%3Csvg%20xmlns%3D%22http://www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22currentColor%22%3E%3Cpath%20d%3D%22M20%204H4c-1.1%200-1.99.9-1.99%202L2%2018c0%201.1.9%202%202%202h16c1.1%200%202-.9%202-2V6c0-1.1-.9-2-2-2zm0%2014H4V8l8%205%208-5v10zm-8-7L4%206h16l-8%205z%22/%3E%3C/svg%3E",
            "COLOR": "#69acc0",
            "SIZE": "90%",
            "POSITION": "center"
        },
        "PLACEMENT_HANDLER": "https://bitrix-3.onrender.com/bitrix/install",
        "ICON_DISABLED": {
            "DATA_IMAGE": "data:image/svg+xml,%3Csvg%20xmlns%3D%22http://www.w3.org/2000/svg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22%2399adb3%22%3E%3Cpath%20d%3D%22M20%204H4c-1.1%200-1.99.9-1.99%202L2%2018c0%201.1.9%202%202%202h16c1.1%200%202-.9%202-2V6c0-1.1-.9-2-2-2zm0%2014H4V8l8%205%208-5v10zm-8-7L4%206h16l-8%205z%22/%3E%3C/svg%3E",
            "COLOR": "#99adb3",
            "SIZE": "90%",
            "POSITION": "center"
        },
        "DEL_EXTERNAL_MESSAGES": True,
        "EDIT_INTERNAL_MESSAGES": True,
        "DEL_INTERNAL_MESSAGES": True,
        "NEWSLETTER": True,
        "NEED_SYSTEM_MESSAGES": True,
        "NEED_SIGNATURE": True,
        "CHAT_GROUP": False,
        "COMMENT": "Настройка канала"
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
                    "name": "Тестовый клиент"
                },
                "chat": {
                    "id": "external-chat-1",
                    "name": "Чат с сайта"
                },
                "message": {
                    "id": "msg-1",
                    "text": "Привет из внешнего сервиса!"
                }
            }
        ]
    }
    return bitrix_app_call("imconnector.send.messages", params)
