import json
import os

from app.models.track import Track


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

def read_Json_file(filename="tracks_data.json"):
    with open(filename, "r") as f:
        data = json.load(f)
    return data

def read_tracks_from_file(data, playlist_id=None) -> list[Track]:
    #print("Data: ",data)
    playlists = data.get("playlists", [])
    tracks = []
    for item in playlists:
        print(f"my id: {playlist_id}")
        itemID = item.get("playlist_id")
        if (playlist_id is not None and itemID != playlist_id) or playlist_id == None:
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