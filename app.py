from flask import Flask, redirect, request, session, jsonify, render_template
from flask_cors import CORS
import requests
import base64

app = Flask(__name__)
app.secret_key = "supersecret"  # any random string

# ====== PUT YOUR SPOTIFY CREDENTIALS HERE ======
CLIENT_ID = "4163144a8b7344d6a57d0a5d478d9353"
CLIENT_SECRET = "53805cb7984c4a3d8bfdae621ddd05be"
# ==============================================
REDIRECT_URI = "http://127.0.0.1:5000/callback"

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

CORS(app, supports_credentials=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    scope = "user-read-email"
    return redirect(
        f"{SPOTIFY_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}"
    )


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: no code returned from Spotify", 400

    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth}"}

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    token_res = requests.post(SPOTIFY_TOKEN_URL, data=data, headers=headers)
    token_data = token_res.json()

    if "access_token" not in token_data:
        return jsonify(token_data), 400

    session["access_token"] = token_data["access_token"]
    return redirect("/")


def get_token():
    return session.get("access_token")


@app.route("/me")
def me():
    token = get_token()
    if not token:
        return jsonify({"error": "not_logged_in"}), 401

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{SPOTIFY_API_BASE}/me", headers=headers)
    return jsonify(res.json())


@app.route("/search")
def search():
    token = get_token()
    if not token:
        return jsonify({"error": "not_logged_in"}), 401

    query = request.args.get("q", "")
    if not query:
        return jsonify({"tracks": {"items": []}})

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": query,
        "type": "track,artist,album",
        "limit": 20,
    }
    res = requests.get(f"{SPOTIFY_API_BASE}/search", headers=headers, params=params)
    return jsonify(res.json())


if __name__ == "__main__":
    app.run(debug=True)
