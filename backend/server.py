from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import base64
import io
import mimetypes
import asyncio
from bson import ObjectId
import gridfs
from pymongo import MongoClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# GridFS for file storage
sync_client = MongoClient(mongo_url)
sync_db = sync_client[os.environ['DB_NAME']]
fs = gridfs.GridFS(sync_db)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class AudioMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    artist: Optional[str] = None
    duration: Optional[float] = None
    file_size: int
    mime_type: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    file_id: str  # GridFS file id
    is_podcast: bool = False

class AudioMetadataCreate(BaseModel):
    title: str
    artist: Optional[str] = None
    duration: Optional[float] = None
    is_podcast: bool = False

class PlaylistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    audio_items: List[str] = []  # List of audio IDs
    created_date: datetime = Field(default_factory=datetime.utcnow)

class PlaylistCreate(BaseModel):
    title: str
    audio_items: List[str] = []

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Skiza Audio Player API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "skiza-audio-player"}

# Audio upload endpoint
@api_router.post("/upload-audio", response_model=AudioMetadata)
async def upload_audio(
    file: UploadFile = File(...),
    title: str = Form(...),
    artist: Optional[str] = Form(None),
    duration: Optional[float] = Form(None),
    is_podcast: bool = Form(False)
):
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read file content
        file_content = await file.read()
        
        # Store in GridFS
        file_id = fs.put(
            file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        # Create metadata
        audio_metadata = AudioMetadata(
            title=title,
            artist=artist,
            duration=duration,
            file_size=len(file_content),
            mime_type=file.content_type,
            file_id=str(file_id),
            is_podcast=is_podcast
        )
        
        # Store metadata in MongoDB
        await db.audio_metadata.insert_one(audio_metadata.dict())
        
        return audio_metadata
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Get all audio files
@api_router.get("/audio", response_model=List[AudioMetadata])
async def get_audio_files():
    try:
        audio_files = await db.audio_metadata.find().to_list(1000)
        return [AudioMetadata(**audio) for audio in audio_files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audio files: {str(e)}")

# Get specific audio file
@api_router.get("/audio/{audio_id}", response_model=AudioMetadata)
async def get_audio_file(audio_id: str):
    try:
        audio = await db.audio_metadata.find_one({"id": audio_id})
        if not audio:
            raise HTTPException(status_code=404, detail="Audio file not found")
        return AudioMetadata(**audio)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audio file: {str(e)}")

# Stream audio file
@api_router.get("/audio/{audio_id}/stream")
async def stream_audio(audio_id: str):
    try:
        # Get metadata
        audio_meta = await db.audio_metadata.find_one({"id": audio_id})
        if not audio_meta:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Get file from GridFS
        file_id = ObjectId(audio_meta["file_id"])
        grid_file = fs.get(file_id)
        
        def generate():
            while True:
                chunk = grid_file.read(8192)
                if not chunk:
                    break
                yield chunk
        
        return StreamingResponse(
            generate(),
            media_type=audio_meta["mime_type"],
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(audio_meta["file_size"]),
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream audio: {str(e)}")

# Delete audio file
@api_router.delete("/audio/{audio_id}")
async def delete_audio(audio_id: str):
    try:
        # Get metadata
        audio_meta = await db.audio_metadata.find_one({"id": audio_id})
        if not audio_meta:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Delete file from GridFS
        file_id = ObjectId(audio_meta["file_id"])
        fs.delete(file_id)
        
        # Delete metadata
        await db.audio_metadata.delete_one({"id": audio_id})
        
        return {"message": "Audio file deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete audio file: {str(e)}")

# Playlist endpoints
@api_router.post("/playlists", response_model=PlaylistItem)
async def create_playlist(playlist: PlaylistCreate):
    try:
        playlist_item = PlaylistItem(
            title=playlist.title,
            audio_items=playlist.audio_items
        )
        await db.playlists.insert_one(playlist_item.dict())
        return playlist_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create playlist: {str(e)}")

@api_router.get("/playlists", response_model=List[PlaylistItem])
async def get_playlists():
    try:
        playlists = await db.playlists.find().to_list(1000)
        return [PlaylistItem(**playlist) for playlist in playlists]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch playlists: {str(e)}")

@api_router.get("/playlists/{playlist_id}", response_model=PlaylistItem)
async def get_playlist(playlist_id: str):
    try:
        playlist = await db.playlists.find_one({"id": playlist_id})
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return PlaylistItem(**playlist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch playlist: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    sync_client.close()