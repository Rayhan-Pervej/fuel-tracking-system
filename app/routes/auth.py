import requests as http
from flask import Blueprint, request, jsonify, current_app
from app.constants import success_response, error_response
from app.extensions import limiter

auth_bp = Blueprint("auth", __name__)


def _token_url():
    url = current_app.config["KEYCLOAK_URL"]
    realm = current_app.config["KEYCLOAK_REALM"]
    return f"{url}/realms/{realm}/protocol/openid-connect/token"


def _logout_url():
    url = current_app.config["KEYCLOAK_URL"]
    realm = current_app.config["KEYCLOAK_REALM"]
    return f"{url}/realms/{realm}/protocol/openid-connect/logout"


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify(error_response(400, "email and password are required")), 400

    client_id = current_app.config["KEYCLOAK_CLIENT_ID"]
    client_secret = current_app.config["KEYCLOAK_CLIENT_SECRET"]


    res = http.post(_token_url(), data={
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": email,
        "password": password,
        "scope": "openid profile",
    })

    if res.status_code == 401:
        return jsonify(error_response(401, "Invalid email or password")), 401
    if not res.ok:
        return jsonify(error_response(502, "Authentication service error")), 502

    tokens = res.json()
    return jsonify(success_response("Login successful", {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "Bearer"
    })), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify(error_response(400, "refresh_token is required")), 400

    client_id = current_app.config["KEYCLOAK_CLIENT_ID"]
    client_secret = current_app.config["KEYCLOAK_CLIENT_SECRET"]

    res = http.post(_token_url(), data={
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    })

    if not res.ok:
        return jsonify(error_response(401, "Invalid or expired refresh token")), 401

    tokens = res.json()
    return jsonify(success_response("Token refreshed", {
        "access_token": tokens["access_token"],
        "token_type": "Bearer"
    })), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify(error_response(400, "refresh_token is required")), 400

    client_id = current_app.config["KEYCLOAK_CLIENT_ID"]
    client_secret = current_app.config["KEYCLOAK_CLIENT_SECRET"]

    http.post(_logout_url(), data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    })

    return jsonify(success_response("Logged out successfully", {})), 200
