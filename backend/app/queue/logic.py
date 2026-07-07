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

from app.auth.spotify import auth_header
from app.models.track_logic import track_objects_from_queue
from app.models.track import Track

def get_queue(token):
    url = "https://api.spotify.com/v1/me/player/queue"
    response = requests.get(url, headers=auth_header(token)).json()
    #print(f"Queue response: {response.get("queue", [])}")
    queue = track_objects_from_queue([response.get("currently_playing", {})] + response.get("queue", []))
    return queue

def top_x_from_queue(queue: list, x: int):
    return queue[0:x]

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

