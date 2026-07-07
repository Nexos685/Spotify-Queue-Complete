import math
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler

from app.models.track import Track

def get_clusters(tracks : list[Track], vibes : list[Track]):
    clusters = []
    for vibe in vibes:
        for track in tracks:
            if track.name == vibe.name:
                print(f"Track: {track.name} by {track.artists} is in cluster {track.cluster}")
                clusters.append(track.cluster)
                break
    return clusters

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

def find_tracks_by_cluster(tracks : list[Track], cluster_id : int) -> list[Track]:
    return [track for track in tracks if track.cluster == cluster_id]

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

def perform_clustering_tracks(tracks : list[Track]):
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