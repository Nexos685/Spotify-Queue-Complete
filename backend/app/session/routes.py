from fastapi import APIRouter, HTTPException
from app.config import SPOTIFY_CLIENT_ID, SPOTIFY_REDIRECT_URI
import urllib.parse
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.auth.spotify import exchange_code_for_token
import uuid

router = APIRouter()

@router.post("/create_session")
def create_session(request: Request, data: dict):
    code = data["code"]
    redirect_uri = data.get("redirect_uri")
    code_verifier = data.get("code_verifier")

    if not all([code, redirect_uri, code_verifier]):
        raise HTTPException(status_code=400, detail="Missing required OAuth parameters")

    #print("GOT THE CODE: ",code)
    tokens = exchange_code_for_token(code, code_verifier, redirect_uri)
    #print("Got the token for the session: ",tokens)
    session_id = str(uuid.uuid4())
    request.app.state.sessions[session_id] = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "tracks": [],  # you will fill this later
    }
    #print("the current session:\n",request.app.state.sessions[session_id])

    return {"session_id": session_id}