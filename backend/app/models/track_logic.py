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

from app.models.track import Track


def make_track_obj(track_data : dict) -> Track:
    track_name = track_data.get("name", "Unknown Track")
    artists = ", ".join(artist["name"] for artist in track_data.get("artists", []))
    track_id = track_data.get("id", "Unknown ID")
    track_isrc = track_data.get("external_ids", {}).get("isrc")
    track_uri = track_data.get("uri", "Unknown URI")
    return Track(name=track_name, artists=artists, id=track_id, isrc=track_isrc, uri=track_uri)

def track_objects_from_queue(queue : list[dict]) -> list[Track]:
    tracks = []
    for item in queue:
        print("QUEUE: \n")
        print(item)
        if item:
            if item.get("is_local", False):
                continue  # Skip local tracks
            track_object = make_track_obj(item)
            tracks.append(track_object)
    return tracks

def track_objects_from_items(items : list[dict]) -> list[Track]:
    tracks = []
    for item in items:
        if item:
            if item.get("is_local", False):
                continue  # Skip local tracks
            track = item.get("item", {})
            track_object = make_track_obj(track)
            tracks.append(track_object)
    return tracks

def find_tracks_by_cluster(tracks : list[Track], cluster_id : int) -> list[Track]:
    return [track for track in tracks if track.cluster == cluster_id]