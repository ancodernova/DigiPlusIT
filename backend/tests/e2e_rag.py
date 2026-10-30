from e2e_auth import BASE_URL, demo_credentials
import requests


def test_pinecone_passport_and_workspace_rag():
    credentials = demo_credentials()
    login = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": credentials["DEMO_EMAIL"], "password": credentials["DEMO_PASSWORD"]},
        timeout=30,
    )
    assert login.ok, login.text
    payload = login.json()
    headers = {"Authorization": f"Bearer {payload['access_token']}", "X-Workspace-ID": payload["workspace"]["_id"]}
    status = requests.get(f"{BASE_URL}/api/v1/pinecone/status", headers=headers, timeout=60)
    assert status.status_code == 200, status.text
    assert status.json()["dimension_matches"] is True
    passport = requests.get(f"{BASE_URL}/api/v1/context-passports/", headers=headers, timeout=30)
    assert passport.status_code == 200
    assert passport.json()
    answer = requests.post(
        f"{BASE_URL}/api/v1/ai/workspace/ask",
        headers=headers,
        json={"question": "Which team agreed on a staged launch?"},
        timeout=90,
    )
    assert answer.status_code == 200, answer.text
    result = answer.json()
    assert "citations" in result
    assert result["citations"]
