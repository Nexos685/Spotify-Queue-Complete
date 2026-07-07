import requests

from app.models.track import Track
from app.config import SOUNDCHARTS_API_KEY,SOUNDCHARTS_APP_ID


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
        "x-api-key": SOUNDCHARTS_API_KEY,
        "x-app-id": SOUNDCHARTS_APP_ID
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