import requests
from flask import current_app


def _base_url():
    url = current_app.config["KEYCLOAK_URL"]
    realm = current_app.config["KEYCLOAK_REALM"]
    return f"{url}/admin/realms/{realm}"


def get_admin_token():
    url = current_app.config["KEYCLOAK_URL"]
    realm = current_app.config["KEYCLOAK_REALM"]
    client_id = current_app.config["KEYCLOAK_ADMIN_CLIENT_ID"]
    client_secret = current_app.config["KEYCLOAK_ADMIN_SECRET"]

    res = requests.post(
        f"{url}/realms/{realm}/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    res.raise_for_status()
    return res.json()["access_token"]


def create_user(name, email, password, role):
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base = _base_url()

    name_parts = name.strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    res = requests.post(f"{base}/users", json={
        "username": email,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": password, "temporary": False}],
    }, headers=headers)
    res.raise_for_status()

    #   returns the new user URL in Location header
    location = res.headers.get("Location", "")
    keycloak_id = location.rstrip("/").split("/")[-1]

    # Assign realm role
    role_res = requests.get(f"{base}/roles/{role}", headers=headers)
    role_res.raise_for_status()
    role_data = role_res.json()

    requests.post(
        f"{base}/users/{keycloak_id}/role-mappings/realm",
        json=[role_data],
        headers=headers,
    ).raise_for_status()

    return keycloak_id


def delete_user(keycloak_id):
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.delete(f"{_base_url()}/users/{keycloak_id}", headers=headers)
    res.raise_for_status()


def update_user(keycloak_id, name=None, email=None):
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {}
    if name:
        name_parts = name.strip().split(" ", 1)
        payload["firstName"] = name_parts[0]
        payload["lastName"] = name_parts[1] if len(name_parts) > 1 else ""
    if email:
        payload["email"] = email
        payload["username"] = email
    if payload:
        requests.put(
            f"{_base_url()}/users/{keycloak_id}",
            json=payload,
            headers=headers,
        ).raise_for_status()
