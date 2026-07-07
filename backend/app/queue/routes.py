import os
import random

from fastapi import APIRouter, Request, HTTPException, status
import numpy as np
from app.auth.spotify import auth_header
from app.models.track import Track
from app.playlist.logic import get_current_playlist_id, get_playlist_tracks
from app.queue.logic import add_list_to_queue, get_queue, top_x_from_queue
from app.features.logic import populate_soundcharts_data_for_tracks
from app.session.logic import get_session
from app.models.track_logic import find_tracks_by_cluster
from app.cluster.logic import get_clusters, perform_clustering_tracks
from data.logic import read_Json_file, read_tracks_from_file, write_tracks_to_file

router = APIRouter()

track_data_file = "data/tracks_data.json"  # Define the path to the tracks data file

@router.get("/finish-queue")
def FinishTheQueue(request:Request, sessionId: str, queueAddLength: int):
    print("session ID: ",sessionId)
    #print(request.app.state.sessions)
    user_session = get_session(request=request,session_id=sessionId)
    #print("\n\n\nUSer session:",user_session)

    if not user_session:
        # Instead of crashing, gracefully tell the mobile app to re-authenticate
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session has expired or is invalid. Please log in again."
        )
    
    token = user_session.get("access_token")
    print("token:",token)

    queue = get_queue(token)
    playlist_id = get_current_playlist_id(token)

    
    if os.path.exists(track_data_file):
        print("Reading tracks from file...")
        read_data = read_Json_file(track_data_file)
        exists = any(
            p.get("playlist_id") == playlist_id
            for p in read_data.get("playlists", [])
        )
        if exists:
            print(read_data.get("playlists", []))
            tracks = read_tracks_from_file(read_data, playlist_id)
            print(f"read tracks: {len(tracks)}")
        else:
            print(f"No tracks found for playlist {playlist_id} in the file. Fetching from Spotify...")
            tracks = get_playlist_tracks(token, playlist_id)
            print("Fetching Soundcharts data for tracks...")
            populate_soundcharts_data_for_tracks(tracks)
            print("Performing clustering on tracks...")
            perform_clustering_tracks(tracks)
            write_tracks_to_file(tracks, playlist_id, track_data_file)
    else:
        print("Track data file not found. Fetching tracks from Spotify...")
        tracks = get_playlist_tracks(token, playlist_id)
        print("Fetching Soundcharts data for tracks...")
        populate_soundcharts_data_for_tracks(tracks)
        print("Performing clustering on tracks...")
        perform_clustering_tracks(tracks)
        write_tracks_to_file(tracks, playlist_id, track_data_file)

    print([track.name for track in tracks])
    vibe_list = top_x_from_queue(queue,4)

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
    random.shuffle(final_queue_possibilities)
    add_list_to_queue(final_queue_possibilities, token, queueAddLength)


    return {
        "status": "success",
        "message": "Queue processed successfully"
    }