import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
KEYCLOAK_URL = "http://localhost:8080"
REALM = "fuel-app"
TEMP_PASSWORD = "12345678"


def get_admin_token():
    # Use master realm admin credentials — full access to manage any realm
    res = requests.post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": "admin",
            "password": "admin",
        },
    )
    res.raise_for_status()
    return res.json()["access_token"]


def ensure_realm_role(base, role_name, headers):
    """Create realm role if it doesn't exist, return role data."""
    res = requests.get(f"{base}/roles/{role_name}", headers=headers)
    if res.status_code == 404:
        requests.post(f"{base}/roles", json={"name": role_name}, headers=headers).raise_for_status()
        res = requests.get(f"{base}/roles/{role_name}", headers=headers)
    res.raise_for_status()
    return res.json()


def migrate():
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()

    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base = f"{KEYCLOAK_URL}/admin/realms/{REALM}"

    # Ensure roles exist before migrating users
    print("Ensuring realm roles exist...")
    for role_name in ["admin", "employee"]:
        role = ensure_realm_role(base, role_name, headers)
        print(f"  [ok] Role '{role_name}' ready (id: {role['id']})")
    print()

    users = list(db.users.find({}))
    print(f"Found {len(users)} users to migrate\n")

    for user in users:
        old_id = user["_id"]
        email = user["email"]
        name = user.get("name", "")
        role = user.get("role", "employee")

        name_parts = name.strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        print(f">> Migrating: {email} (old_id: {old_id})")

        # 1. Create user in Keycloak (idempotent — fetch if already exists)
        res = requests.post(f"{base}/users", json={
            "username": email,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "emailVerified": True,
            "credentials": [{"type": "password", "value": TEMP_PASSWORD, "temporary": False}],
        }, headers=headers)

        if res.status_code == 409:
            # Already exists in Keycloak — fetch by email
            existing = requests.get(f"{base}/users", params={"email": email, "exact": "true"}, headers=headers)
            existing.raise_for_status()
            keycloak_id = existing.json()[0]["id"]
            print(f"  [exists] Already in Keycloak: {keycloak_id}")
        else:
            res.raise_for_status()
            keycloak_id = res.headers["Location"].rstrip("/").split("/")[-1]
            print(f"  [created] Keycloak ID: {keycloak_id}")

        # 2. Assign realm role
        role_data = ensure_realm_role(base, role, headers)
        requests.post(
            f"{base}/users/{keycloak_id}/role-mappings/realm",
            json=[role_data],
            headers=headers,
        ).raise_for_status()

        # 3. Update all references in other collections BEFORE touching users
        r1 = db.pump_employees.update_many({"user_id": old_id}, {"$set": {"user_id": keycloak_id}})
        r2 = db.pump_employees.update_many({"added_by": old_id}, {"$set": {"added_by": keycloak_id}})
        r3 = db.vehicles.update_many({"user_id": old_id}, {"$set": {"user_id": keycloak_id}})

        # 4. Delete old user doc first (frees up the unique email index)
        db.users.delete_one({"_id": old_id})

        # 5. Insert new MongoDB user doc with keycloak_id, strip stale fields (idempotent)
        if not db.users.find_one({"_id": keycloak_id}):
            new_user = {k: v for k, v in user.items() if k not in ("password_hash", "license")}
            new_user["_id"] = keycloak_id
            db.users.insert_one(new_user)

        print(f"  [ok] Keycloak ID: {keycloak_id}")
        print(f"  [ok] pump_employees.user_id updated: {r1.modified_count}")
        print(f"  [ok] pump_employees.added_by updated: {r2.modified_count}")
        print(f"  [ok] vehicles.user_id updated: {r3.modified_count}")
        print()

    print("Migration complete.")


if __name__ == "__main__":
    migrate()
