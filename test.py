import http.server
import socket
import socketserver
import urllib.parse
import webbrowser
import requests
import time
import os
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

load_dotenv()

QUEUE_ADD_LENGTH = 10
RECLUSTER = False

##spotify API credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
##getbpm API credentials
GETBPM_KEY = os.getenv("GETBPM_KEY")

##soundcharts keys
soundcharts_api_key = os.getenv("SOUNDCHARTS_API_KEY")
soundcharts_app_id = os.getenv("SOUNDCHARTS_APP_ID")

SCOPES = (
    "user-read-playback-state "
    "user-read-currently-playing "
    "user-modify-playback-state "
    "playlist-read-private "
    "playlist-read-collaborative"
)

class IPv6TCPServer(socketserver.TCPServer):
    address_family = socket.AF_INET6

class Track:
    def __init__(self, name, artists, id, isrc, uri, cluster=None):
        self.name = name
        self.artists = artists
        self.id = id
        self.isrc = isrc
        self.uri = uri
        self.cluster = cluster
        self.features = {
            "acousticness": None,
            "danceability": None,
            "energy": None,
            "instrumentalness": None,
            "key": None,
            "liveness": None,
            "loudness": None,
            "mode": None,
            "speechiness": None,
            "tempo": None,
            "timeSignature": None,
            "valence": None,
            "true_key": None,
            "key_sin" :None,
            "key_cos" : None
        }

def pretty(data):
    print(json.dumps(data, indent=4, sort_keys=True))
# ---------------------------------------------------------
# Build Spotify login URL
# ---------------------------------------------------------
def build_auth_url():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI
    }
    return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)

# ---------------------------------------------------------
# Exchange code for tokens
# ---------------------------------------------------------
def exchange_code_for_token(code):
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    r = requests.post(url, data=data)
    return r.json()

# ---------------------------------------------------------
# Refresh access token
# ---------------------------------------------------------
def refresh_access_token(refresh_token):
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    r = requests.post(url, data=data)
    return r.json()

# ---------------------------------------------------------
# API helpers
# ---------------------------------------------------------
def auth_header(token):
    return {"Authorization": f"Bearer {token}"}

# ---------------------------------------------------------
# song and context functions
# ---------------------------------------------------------

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

# ---------------------------------------------------------
# Queue Functions
# ---------------------------------------------------------
def get_queue(token):
    url = "https://api.spotify.com/v1/me/player/queue"
    response = requests.get(url, headers=auth_header(token)).json()
    #print(f"Queue response: {response.get("queue", [])}")
    queue = track_objects_from_queue([response.get("currently_playing", {})] + response.get("queue", []))
    return queue

def add_to_queue(token, uri):
    url = "https://api.spotify.com/v1/me/player/queue"
    return requests.post(url, headers=auth_header(token), params={"uri": uri}).json()

def add_list_to_queue(tracks : list[Track], token, songs_count):
    for track in tracks[:songs_count]:
        if track.uri:
            url = f"https://api.spotify.com/v1/me/player/queue?uri={track.uri}"
            response = requests.post(url, headers=auth_header(token))
            if response.status_code != 204 and response.status_code != 200:
                print(f"Failed to add {track.name} by {track.artists} to queue. Status code: {response.status_code}")
            else:
                print(f"Added {track.name} by {track.artists} to queue.")
        else:
            print(f"Skipping {track.name} by {track.artists} due to missing URI.")

# ---------------------------------------------------------
# Track Object Extraction
# ---------------------------------------------------------
def track_objects_from_items(items : list[dict]) -> list[Track]:
    tracks = []
    for item in items:
        if item.get("is_local", False):
            continue  # Skip local tracks
        track = item.get("item", {})
        track_object = make_track_obj(track)
        tracks.append(track_object)
    return tracks

def track_objects_from_queue(queue : list[dict]) -> list[Track]:
    tracks = []
    for item in queue:
        if item.get("is_local", False):
            continue  # Skip local tracks
        track_object = make_track_obj(item)
        tracks.append(track_object)
    return tracks

def make_track_obj(track_data : dict) -> Track:
    track_name = track_data.get("name", "Unknown Track")
    artists = ", ".join(artist["name"] for artist in track_data.get("artists", []))
    track_id = track_data.get("id", "Unknown ID")
    track_isrc = track_data.get("external_ids", {}).get("isrc")
    track_uri = track_data.get("uri", "Unknown URI")
    return Track(name=track_name, artists=artists, id=track_id, isrc=track_isrc, uri=track_uri)

def populate_track_features_spotify(token, tracks : list[Track]) -> list[Track]:
    valid_tracks = [t for t in tracks if t.id and isinstance(t.id, str) and len(t.id) == 22]
    invalid_tracks = [t for t in tracks if t not in valid_tracks]
    ids = [track.id for track in valid_tracks]
    print(len(ids))
    offset = 0
    limit = 100
    while True:
        if offset + limit > len(ids):
            limit = len(ids) - offset
        url = f"https://api.spotify.com/v1/audio-features?ids={','.join(ids[offset:offset+limit])}"
        response = requests.get(url, headers=auth_header(token))
        print(response.status_code, response.json())
        features = response.get("audio_features", [])[i - offset]
        if(len(features) < 1):
            return valid_tracks
        print(response)
        for i in range(offset, offset + len(features)):
            track = valid_tracks[i]
            track.features.update({
                "danceability": features.get("danceability"),
                "energy": features.get("energy"),
                "key": features.get("key"),
                "loudness": features.get("loudness"),
                "mode": features.get("mode"),
                "speechiness": features.get("speechiness"),
                "acousticness": features.get("acousticness"),
                "instrumentalness": features.get("instrumentalness"),
                "liveness": features.get("liveness"),
                "valence": features.get("valence"),
                "tempo": features.get("tempo")
            })
        offset += len(response)

# ---------------------------------------------------------
# Playlist Functions
# ---------------------------------------------------------

def get_playlist_data(token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    response = requests.get(url, headers=auth_header(token)).json()
    return response

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

def get_playlist_name(playlist):
    return playlist.get("name", "Unknown Playlist")

def get_tracks_names(track_item_list : list[Track]) -> list[str]:
    tracks = []
    for track in track_item_list:
        track_name = track.name
        artists = track.artists
        tracks.append(f"{track_name} by {artists}")
    return tracks

# ---------------------------------------------------------
# getsongbpm api functions
# ---------------------------------------------------------
def populate_features_for_track(track : Track):
    url = f"https://api.getsong.co/search/"
    params = {
        "api_key": GETBPM_KEY,
        "type": "both",
        "lookup": f"song:{track.name} artist:{track.artists}"
    }
    response = requests.get(url,params=params)
    if response.status_code != 200:
        print(f"Error fetching features for {track.name}: {response.status_code}")
        return None
    data = response.json()
    data = data.get("search", {})[0] if data.get("search") else None
    if not data:
        print(f"No features found for {track.name}")
        return None
    track.features.update({
        "bpm": data.get("tempo"),
        "key": data.get("key_of"),
        "open_key": data.get("open_key"),
        "danceability": data.get("danceability"),
        "acousticness": data.get("acousticness"),
    })


# ---------------------------------------------------------
# Soundcharts API functions
# ---------------------------------------------------------

def populate_soundcharts_data_for_track(track : Track, soundcharts_data : dict):
    soundcharts_data = soundcharts_data.get("object", {}).get("audio", {})
    #print(soundcharts_data)
    track.features.update({
        "acousticness": soundcharts_data.get("acousticness"),
        "danceability": soundcharts_data.get("danceability"),
        "energy": soundcharts_data.get("energy"),
        "instrumentalness": soundcharts_data.get("instrumentalness"),
        "key": soundcharts_data.get("key"),
        "liveness": soundcharts_data.get("liveness"),
        "loudness": soundcharts_data.get("loudness"),
        "mode": soundcharts_data.get("mode"),
        "speechiness": soundcharts_data.get("speechiness"),
        "tempo": soundcharts_data.get("tempo"),
        "timeSignature": soundcharts_data.get("timeSignature"),
        "valence": soundcharts_data.get("valence")
    })

def get_soundcharts_data_for_track(track : Track):
    headers = {
        "x-api-key": soundcharts_api_key,
        "x-app-id": soundcharts_app_id
    }

    #print(f"Fetching Soundcharts data for {track.name} (ISRC: {track.isrc})...")

    url = f"https://customer.api.soundcharts.com/api/v2.25/song/by-isrc/{track.isrc}"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching Soundcharts data for {track.name}: {response.status_code}")
        return None
    data = response.json()
    return data

def populate_soundcharts_data_for_tracks(tracks : list[Track]):
    count = 0
    for track in tracks:
        if track.isrc == None:
            print(f"Skipping {track.name} by {track.artists} due to missing ISRC.")
            continue
        print(f"\r{' ' * 50}", end="") 
        print(f"\rProcessing track {count + 1}/{len(tracks)}: {track.name} by {track.artists}", end="", flush=True)
        count += 1
        soundcharts_data = get_soundcharts_data_for_track(track)
        if soundcharts_data:
            populate_soundcharts_data_for_track(track, soundcharts_data)

# ---------------------------------------------------------
# file handling
# ---------------------------------------------------------

def write_tracks_to_file(tracks : list[Track], playlist_id : str, filename="tracks_data.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            playlist_data = json.load(f)
    else:
        playlist_data = {"playlists": []}

    tracks_data = []
    print(f"writing {len(tracks)} tracks")
    print(f"playlist: {playlist_id}")
    for track in tracks:
        track_data = {
            "name": track.name,
            "artists": track.artists,
            "id": track.id,
            "isrc": track.isrc,
            "uri": track.uri,
            "cluster": track.cluster,
            "features": track.features
        }
        tracks_data.append(track_data)
    if playlist_id == None: playlist_id = "null"
    playlist_entry = {
        "playlist_id" : playlist_id,
        "tracks" : tracks_data
    }
    
    playlist_data["playlists"] = [
        p for p in playlist_data["playlists"] if p["playlist_id"] != playlist_id]

    playlist_data["playlists"].append(playlist_entry)
    with open(filename, "w") as f:
        json.dump(playlist_data, f, indent=4)

def read_tracks_from_file(filename="tracks_data.json", playlist_id=None) -> list[Track]:
    with open(filename, "r") as f:
        data = json.load(f)
    playlists = data.get("playlists", [])
    tracks = []
    for item in playlists:
        print(f"my id: {playlist_id}")
        
        if playlist_id is not None and item.get("playlist_id") != playlist_id:
            continue
        print(f"accepted id: {item.get('playlist_id')}")
        for track_data in item.get("tracks", []):
            track = Track(
                name=track_data["name"],
                artists=track_data["artists"],
                id=track_data["id"],
                isrc=track_data["isrc"],
                uri = track_data.get("uri", None),
                cluster = track_data.get("cluster", None)
            )
            track.features = track_data.get("features", {})
            tracks.append(track)

    return tracks

# ---------------------------------------------------------
# feature transformation and visualization
# ---------------------------------------------------------
def plot_interactive(X, labels, names):
    fig = px.scatter(
        x=X[:, 0],
        y=X[:, 1],
        color=labels.astype(str),
        hover_name=names,
        title="Interactive Embedding"
    )
    fig.show()

def plot_interactive_3d(X, labels, names):
    fig = px.scatter_3d(
    x=X[:, 0],
    y=X[:, 1],
    z=X[:, 2],
    color=labels.astype(str),
    hover_name=names,
    opacity=0.85,
    title="3D UMAP Embedding"
    )

    fig.show()
    

def assign_true_key(track : Track):
    key = track.features.get("key")
    mode = track.features.get("mode")
    if key is None or mode is None:
        track.features.update({"true_key": None})
    if mode == 1:  # Major
        track.features.update({"true_key": key})
    elif mode == 0:  # Minor
        track.features.update({"true_key": key-0.5})  # Convert to relative major
    else:
        track.features.update({"true_key": None})

def encode_key_cyclic(key):
    angle = 2 * math.pi * (key / 12)
    return math.sin(angle), math.cos(angle)

def assign_cyclic_key(track,key_sin,key_cos):
    track.features.update({"key_sin": key_sin,
                          "key_cos": key_cos})

def transform_keys(tracks : list[Track]):
    for track in tracks:
        assign_true_key(track)
        key_sin,key_cos = encode_key_cyclic(track.features.get("true_key", None))
        assign_cyclic_key(track,key_sin,key_cos)


def extract_feature_matrix(tracks):
    feature_names = list(tracks[0].features.keys())
    feature_names.remove("key")
    feature_names.remove("mode")
    feature_names.remove("true_key")
    #feature_names.remove("loudness")
    #feature_names.remove("speechiness")
    #feature_names.remove("instrumentalness")
    #feature_names.remove("liveness")
    print(feature_names)
    matrix = np.array([
        [tr.features[name] for name in feature_names]
        for tr in tracks
    ])
    return matrix, feature_names

def get_clusters(tracks : list[Track], names : list[str]):
    clusters = []
    for name in names:
        for track in tracks:
            if track.name == name:
                print(f"Track: {track.name} by {track.artists} is in cluster {track.cluster}")
                clusters.append(track.cluster)
                break
    return clusters

def find_tracks_by_cluster(tracks : list[Track], cluster_id : int) -> list[Track]:
    return [track for track in tracks if track.cluster == cluster_id]

# ---------------------------------------------------------
# cluster functions
# ---------------------------------------------------------

def get_all_clusters_dict(tracks : list[Track]) -> dict:
    clusters = {}
    print(len(tracks))
    i = 0
    for track in tracks:
        i+=1
        clusters.setdefault(track.cluster, []).append(track)
    print(f"loops: {i}")
    return clusters


# ---------------------------------------------------------
# HTTP callback handler
# ---------------------------------------------------------
class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/callback":
            code = urllib.parse.parse_qs(parsed.query).get("code", [None])[0]

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"You can close this window.")

            print("\nAuthorization code:", code)
            tokens = exchange_code_for_token(code)

            access_token = tokens["access_token"]
            refresh_token = tokens.get("refresh_token")

            print("\nAccess Token:", access_token)
            print("Refresh Token:", refresh_token)

            print("\n=== CURRENTLY PLAYING ===")
            (currently_playing,playlist_id) = get_currently_playing(access_token)
            print(currently_playing.name if currently_playing != "Nothing is playing" else currently_playing)
            #currently_playing_features = populate_features_for_track(currently_playing)

            print("\n=== Playlist ===")
            playlist = get_playlist_data(access_token, playlist_id)
            print(playlist.get("owner", {}))

            if not os.path.exists("tracks_data.json"):
                tracks = get_playlist_tracks(access_token, playlist_id)
                populate_soundcharts_data_for_tracks(tracks)
                write_tracks_to_file(tracks, playlist_id)
            else:
                tracks = read_tracks_from_file("tracks_data.json", playlist_id)
                print(f"read tracks: {len(tracks)}")
            
                if RECLUSTER:
                    transform_keys(tracks)
                    matrix, feature_names = extract_feature_matrix(tracks)
                    scaler = MinMaxScaler()
                    scaled_matrix = scaler.fit_transform(np.asarray(matrix))
                    print(f"Scaled feature matrix:\n{scaled_matrix}")

                   
                    #embedding = umap.UMAP(n_neighbors=25, min_dist=0.1,n_components = 3).fit_transform(scaled_matrix)
                    embedding = scaled_matrix
                    print(f"UMAP embedding:\n{embedding}")
                    #labels = hdbscan.HDBSCAN(min_cluster_size=3, min_samples=2).fit_predict(embedding)

                    k = 25
                    model = KMeans(n_clusters=k).fit(embedding)
                    model.fit(embedding)
                    labels = model.labels_

                    for track, label in zip(tracks, labels):
                        track.cluster = int(label)
                    write_tracks_to_file(tracks, playlist_id)
                    names = [track.name for track in tracks]
                    #plot_interactive_3d(embedding,labels,names)

            print("/n=== Clusters ===")
            clusters = get_all_clusters_dict(tracks)
            for cluster in clusters.keys():
                print(f"\n\nCluster {cluster}: {[track.name for track in clusters[cluster]]}")


            print("\n=== QUEUE ===")
            queue = get_queue(access_token)
            next_three = queue[1:4]
            print(f"Next three tracks in the queue: {[track.name for track in next_three]}")
            print([currently_playing.name] + [track.name for track in next_three])
            vibe_list = [currently_playing.name] + [track.name for track in next_three]
            clusters = get_clusters(tracks, vibe_list)
            print(f"Found {len(clusters)} tracks in the playlist that match the currently playing track and the next three tracks in the queue.")
            clusters = np.unique(clusters)
            print(f"Unique clusters: {clusters}")
            queue_possibilities = []
            outliers = []
            for cluster in clusters:
                if cluster != -1:   #disregard outliers
                    queue_possibilities.extend(find_tracks_by_cluster(tracks, cluster))
            outliers.extend(find_tracks_by_cluster(tracks,-1))
            ## remove songs we already have from the queue possibilities
            
            final_queue_possibilities = [track for track in queue_possibilities if track.name not in vibe_list]
            #print(len(queue_possibilities))
            print("outliers: "+str(len(outliers)))
            random.shuffle(queue_possibilities)
            add_list_to_queue(queue_possibilities, access_token, QUEUE_ADD_LENGTH)

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    print("\n=== SPOTIFY LOGIN ===\n")

    auth_url = build_auth_url()
    print("Opening browser for Spotify login...")
    webbrowser.open(auth_url)

    with IPv6TCPServer(("::1", 8000), CallbackHandler) as httpd:
        print("Waiting for Spotify redirect...")
        time.sleep(1)  # Give the server a moment to start
        httpd.handle_request()
