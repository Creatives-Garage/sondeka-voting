import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Audio Player Component
const AudioPlayer = ({ audioFiles, currentTrack, onTrackChange }) => {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (audio && currentTrack) {
      audio.src = `${API}/audio/${currentTrack.id}/stream`;
      setIsLoading(true);
    }
  }, [currentTrack]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const setAudioData = () => {
      setDuration(audio.duration);
      setCurrentTime(audio.currentTime);
      setIsLoading(false);
    };

    const setAudioTime = () => setCurrentTime(audio.currentTime);

    const handleEnded = () => {
      setIsPlaying(false);
      // Auto-play next track
      const currentIndex = audioFiles.findIndex(file => file.id === currentTrack.id);
      if (currentIndex < audioFiles.length - 1) {
        onTrackChange(audioFiles[currentIndex + 1]);
      }
    };

    audio.addEventListener('loadeddata', setAudioData);
    audio.addEventListener('timeupdate', setAudioTime);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('loadeddata', setAudioData);
      audio.removeEventListener('timeupdate', setAudioTime);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [currentTrack, audioFiles, onTrackChange]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e) => {
    const audio = audioRef.current;
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    audio.currentTime = pos * audio.duration;
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    audioRef.current.volume = newVolume;
  };

  const formatTime = (time) => {
    if (isNaN(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const nextTrack = () => {
    const currentIndex = audioFiles.findIndex(file => file.id === currentTrack.id);
    if (currentIndex < audioFiles.length - 1) {
      onTrackChange(audioFiles[currentIndex + 1]);
    }
  };

  const prevTrack = () => {
    const currentIndex = audioFiles.findIndex(file => file.id === currentTrack.id);
    if (currentIndex > 0) {
      onTrackChange(audioFiles[currentIndex - 1]);
    }
  };

  return (
    <div className="audio-player">
      <audio ref={audioRef} />
      
      {/* Track Info */}
      <div className="track-info">
        <h3 className="track-title">{currentTrack?.title || "No track selected"}</h3>
        <p className="track-artist">{currentTrack?.artist || "Unknown artist"}</p>
      </div>

      {/* Controls */}
      <div className="controls">
        <button onClick={prevTrack} className="control-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
          </svg>
        </button>
        
        <button onClick={togglePlayPause} className="play-pause-btn" disabled={!currentTrack || isLoading}>
          {isLoading ? (
            <div className="loading-spinner"></div>
          ) : isPlaying ? (
            <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
            </svg>
          ) : (
            <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          )}
        </button>
        
        <button onClick={nextTrack} className="control-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
          </svg>
        </button>
      </div>

      {/* Progress Bar */}
      <div className="progress-container">
        <span className="time-display">{formatTime(currentTime)}</span>
        <div className="progress-bar" onClick={handleSeek}>
          <div 
            className="progress-fill" 
            style={{ width: `${(currentTime / duration) * 100}%` }}
          ></div>
        </div>
        <span className="time-display">{formatTime(duration)}</span>
      </div>

      {/* Volume Control */}
      <div className="volume-control">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
        </svg>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={volume}
          onChange={handleVolumeChange}
          className="volume-slider"
        />
      </div>
    </div>
  );
};

// File Upload Component
const FileUpload = ({ onUploadSuccess }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    uploadFiles(files);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    uploadFiles(files);
  };

  const uploadFiles = async (files) => {
    setUploading(true);
    
    for (const file of files) {
      if (!file.type.startsWith('audio/')) {
        alert(`${file.name} is not an audio file`);
        continue;
      }

      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.replace(/\.[^/.]+$/, ""));
      formData.append('artist', 'Unknown Artist');
      formData.append('is_podcast', false);

      try {
        await axios.post(`${API}/upload-audio`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } catch (error) {
        console.error('Upload failed:', error);
        alert(`Failed to upload ${file.name}`);
      }
    }
    
    setUploading(false);
    onUploadSuccess();
  };

  return (
    <div className="upload-section">
      <div
        className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="audio/*"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        
        {uploading ? (
          <div className="upload-loading">
            <div className="loading-spinner"></div>
            <p>Uploading...</p>
          </div>
        ) : (
          <div className="upload-content">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            <p>Drag & drop audio files here or click to select</p>
            <p className="upload-hint">Supports MP3, WAV, M4A, and more</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Track List Component
const TrackList = ({ audioFiles, currentTrack, onTrackSelect, onDeleteTrack }) => {
  return (
    <div className="track-list">
      <h3>Your Music Library</h3>
      {audioFiles.length === 0 ? (
        <p className="empty-state">No audio files uploaded yet</p>
      ) : (
        <div className="tracks">
          {audioFiles.map((track) => (
            <div
              key={track.id}
              className={`track-item ${currentTrack?.id === track.id ? 'active' : ''}`}
              onClick={() => onTrackSelect(track)}
            >
              <div className="track-details">
                <h4>{track.title}</h4>
                <p>{track.artist}</p>
                <span className="track-type">{track.is_podcast ? 'Podcast' : 'Music'}</span>
              </div>
              <button 
                className="delete-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteTrack(track.id);
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [audioFiles, setAudioFiles] = useState([]);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAudioFiles = async () => {
    try {
      const response = await axios.get(`${API}/audio`);
      setAudioFiles(response.data);
      if (response.data.length > 0 && !currentTrack) {
        setCurrentTrack(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to fetch audio files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTrack = async (trackId) => {
    try {
      await axios.delete(`${API}/audio/${trackId}`);
      setAudioFiles(audioFiles.filter(track => track.id !== trackId));
      if (currentTrack?.id === trackId) {
        setCurrentTrack(audioFiles.find(track => track.id !== trackId) || null);
      }
    } catch (error) {
      console.error('Failed to delete track:', error);
    }
  };

  useEffect(() => {
    fetchAudioFiles();
  }, []);

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading Skiza...</p>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="skiza-container">
        <header className="app-header">
          <h1 className="app-title">Skiza</h1>
          <p className="app-subtitle">Your Audio Player</p>
        </header>

        <main className="main-content">
          <FileUpload onUploadSuccess={fetchAudioFiles} />
          
          <div className="player-section">
            <AudioPlayer
              audioFiles={audioFiles}
              currentTrack={currentTrack}
              onTrackChange={setCurrentTrack}
            />
          </div>

          <TrackList
            audioFiles={audioFiles}
            currentTrack={currentTrack}
            onTrackSelect={setCurrentTrack}
            onDeleteTrack={handleDeleteTrack}
          />
        </main>
      </div>
    </div>
  );
}

export default App;