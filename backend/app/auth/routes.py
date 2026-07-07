import secrets
import hashlib
import base64
from fastapi import APIRouter
from app.config import SPOTIFY_CLIENT_ID, SPOTIFY_REDIRECT_URI
import urllib.parse
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.auth.spotify import exchange_code_for_token
import uuid

router = APIRouter()

def base64url(input_bytes):
    return base64.urlsafe_b64encode(input_bytes).rstrip(b"=").decode()

SCOPES = (
    "user-read-playback-state "
    "user-read-currently-playing "
    "user-modify-playback-state "
    "playlist-read-private "
    "playlist-read-collaborative"
)

@router.get("/login-url")
async def get_login_url(request: Request):
    client_id = SPOTIFY_CLIENT_ID
    redirect_uri = SPOTIFY_REDIRECT_URI  # you override this in the app

    # PKCE
    verifier = secrets.token_urlsafe(64)
    challenge = base64url(hashlib.sha256(verifier.encode()).digest())

    # state
    session_id = secrets.token_hex(16)

    # store verifier for later token exchange
    request.app.state.sessions[session_id] = {
        "verifier": verifier,
        "tokens": None,
    }

    scopes = " ".join([
        "user-read-playback-state",
        "user-read-currently-playing",
        "user-modify-playback-state",
        "playlist-read-private",
        "playlist-read-collaborative",
    ])

    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
        "state": session_id,
    }

    # build URL
    from urllib.parse import urlencode
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"

    return {
        "auth_url": auth_url,
        "session_id": session_id,
        "redirect_uri": redirect_uri,
    }

@router.get("/callback", response_class=HTMLResponse)
async def callback(request: Request, code: str):
    tokens = exchange_code_for_token(code)

    session_id = str(uuid.uuid4())
    request.app.state.sessions[session_id] = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "tracks": [],  # you will fill this later
    }

    return HTMLResponse(f"""
    <html>
    <body>
    <script>
    window.location.href = "myapp://auth?session_id={session_id}";
    </script>
    </body>
    </html>
    """)



