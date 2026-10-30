from e2e_auth import BASE_URL, demo_credentials
import requests


def token():
    credentials = demo_credentials()
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": credentials["DEMO_EMAIL"], "password": credentials["DEMO_PASSWORD"]},
        timeout=30,
    )
    assert response.ok, response.text
    return response.json()["access_token"], response.json()["workspace"]["_id"]


def test_workspace_meetings_tasks_knowledge_persisted():
    access_token, workspace_id = token()
    headers = {"Authorization": f"Bearer {access_token}", "X-Workspace-ID": workspace_id}
    for path in ("/api/v1/dashboard/overview", "/api/v1/meetings/", "/api/v1/tasks/", "/api/v1/knowledge/", "/api/v1/context-passports/"):
        response = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=30)
        assert response.status_code == 200, (path, response.text)
    meetings = requests.get(f"{BASE_URL}/api/v1/meetings/", headers=headers, timeout=30).json()
    tasks = requests.get(f"{BASE_URL}/api/v1/tasks/", headers=headers, timeout=30).json()
    documents = requests.get(f"{BASE_URL}/api/v1/knowledge/", headers=headers, timeout=30).json()
    assert len(meetings) >= 8
    assert len(tasks) >= 20
    assert len(documents) >= 4
    cross_workspace = requests.get(
        f"{BASE_URL}/api/v1/meetings/",
        headers={"Authorization": f"Bearer {access_token}", "X-Workspace-ID": "000000000000000000000001"},
        timeout=30,
    )
    assert cross_workspace.status_code in (403, 404)
