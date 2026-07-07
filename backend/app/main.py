from fastapi import FastAPI
from app.auth.routes import router as auth_router
from app.playlist.routes import router as playlist_router
from app.queue.routes import router as queue_router
from app.cluster.routes import router as cluster_router
from app.session.routes import router as session_router

app = FastAPI()
app.state.sessions = {}

app.include_router(auth_router, prefix="/auth")
app.include_router(playlist_router, prefix="/playlist")
app.include_router(queue_router, prefix="/queue")
app.include_router(cluster_router, prefix="/cluster")
app.include_router(session_router,prefix="/session")
