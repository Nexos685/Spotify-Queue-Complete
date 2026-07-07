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
            "key_sin": None,
            "key_cos": None
        }
