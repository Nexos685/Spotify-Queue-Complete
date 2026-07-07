from fastapi import APIRouter
from app.config import SPOTIFY_CLIENT_ID, SPOTIFY_REDIRECT_URI
import urllib.parse
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.auth.spotify import exchange_code_for_token
import uuid

def get_session(request: Request, session_id):
    return request.app.state.sessions.get(session_id)

