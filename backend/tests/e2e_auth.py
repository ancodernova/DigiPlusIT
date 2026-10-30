import os
from pathlib import Path

import requests


BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")


def demo_credentials():
    values = {}
    for line in (Path(__file__).parents[1] / ".demo-credentials").read_text(encoding="utf-8-sig").splitlines():
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def test_login_me_and_invalid_jwt():
    credentials = demo_credentials()
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": credentials["DEMO_EMAIL"], "password": credentials["DEMO_PASSWORD"]},
        timeout=30,
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    me = requests.get(f"{BASE_URL}/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=30)
    assert me.status_code == 200
    assert me.json()["email"] == credentials["DEMO_EMAIL"]
    denied = requests.get(f"{BASE_URL}/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}, timeout=30)
    assert denied.status_code == 401
