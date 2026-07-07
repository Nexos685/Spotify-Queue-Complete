from fastapi import APIRouter
from app.auth.spotify import auth_header
from app.models.track import Track
from app.playlist.logic import get_playlist_tracks

router = APIRouter()