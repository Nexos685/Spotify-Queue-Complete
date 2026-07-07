
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import sklearn
from sklearn.cluster import KMeans
import random
import json
import math
from dotenv import load_dotenv

from app.auth.spotify import auth_header
from app.models.track_logic import track_objects_from_items
from app.models.track import Track


def get_playlist_tracks(token, playlist_id) -> list[Track]:
    print(f"playlist_id: {playlist_id}")
    offset = 0
    limit = 100

    tracks = []

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items"

    while True:
        params = {"offset": offset, "limit": limit}
        response = requests.get(url, headers=auth_header(token),params=params).json()
        items = track_objects_from_items(response.get("items", {}))
        tracks.extend(items)
        if len(items) < 1:
            break
        offset += len(items)

    print(f"Extracted {len(tracks)} tracks from playlist.")
    return tracks

def get_current_playlist_id(token) -> str: 
    (currently_playing,playlist_id) = get_currently_playing(token)
    if currently_playing == None:
        print("Nothing is currently Playing")
    if playlist_id == None:
        print("No playlist ID obtainable")
    return playlist_id

def get_currently_playing(token) -> tuple[Track, str | None]:
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    response =  requests.get(url, headers=auth_header(token))
    print(f"status code: {response.status_code}")
    if response.status_code == 204:
        return ("Nothing is playing", None)
    response = response.json()
    current_track = track_objects_from_items([response])
    current_track = current_track[0] if current_track else None
    print("Device:")
    print(response)
    #return current_track, None
    return current_track, response.get("context", {}).get("uri", "No context").split(":")[-1] if response.get("context", {}).get("uri") else None
