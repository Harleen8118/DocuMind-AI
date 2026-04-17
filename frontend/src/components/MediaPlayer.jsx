import { useEffect, useRef, useState, useCallback } from 'react';
import { Play, Pause, Volume2, VolumeX, SkipBack, SkipForward } from 'lucide-react';

export default function MediaPlayer({ document, seekTo }) {
  const mediaRef = useRef(null);
  const waveformRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(0.8);

  const isVideo = document?.file_type === 'video';
  const mediaUrl = document?.filename ? `/uploads/${document.filename}` : null;

  // Seek to timestamp when prop changes
  useEffect(() => {
    if (seekTo !== undefined && seekTo !== null && mediaRef.current) {
      mediaRef.current.currentTime = seekTo;
      if (!isPlaying) {
        mediaRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
    }
  }, [seekTo]);

  const handleTimeUpdate = useCallback(() => {
    if (mediaRef.current) {
      setCurrentTime(mediaRef.current.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (mediaRef.current) {
      setDuration(mediaRef.current.duration);
    }
  }, []);

  const togglePlay = useCallback(() => {
    if (!mediaRef.current) return;
    if (isPlaying) {
      mediaRef.current.pause();
    } else {
      mediaRef.current.play().catch(() => {});
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const toggleMute = useCallback(() => {
    if (mediaRef.current) {
      mediaRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  }, [isMuted]);

  const handleVolumeChange = useCallback((e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (mediaRef.current) {
      mediaRef.current.volume = newVolume;
    }
  }, []);

  const handleSeek = useCallback((e) => {
    const pos = parseFloat(e.target.value);
    if (mediaRef.current) {
      mediaRef.current.currentTime = pos;
      setCurrentTime(pos);
    }
  }, []);

  const skipForward = useCallback(() => {
    if (mediaRef.current) {
      mediaRef.current.currentTime = Math.min(mediaRef.current.currentTime + 10, duration);
    }
  }, [duration]);

  const skipBackward = useCallback(() => {
    if (mediaRef.current) {
      mediaRef.current.currentTime = Math.max(mediaRef.current.currentTime - 10, 0);
    }
  }, []);

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = duration ? (currentTime / duration) * 100 : 0;

  if (!mediaUrl) return null;

  return (
    <div className="p-4 border-b border-surface-800">
      <h3 className="text-sm font-semibold text-surface-300 mb-3 flex items-center gap-2">
        {isVideo ? '🎬' : '🎵'} Media Player
      </h3>

      {/* Video element */}
      {isVideo && (
        <div className="rounded-xl overflow-hidden bg-black mb-3 aspect-video">
          <video
            ref={mediaRef}
            src={mediaUrl}
            className="w-full h-full object-contain"
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
          />
        </div>
      )}

      {/* Audio element (hidden) */}
      {!isVideo && (
        <audio
          ref={mediaRef}
          src={mediaUrl}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
        />
      )}

      {/* Waveform / Progress bar */}
      <div className="mb-3">
        <div className="relative h-2 bg-surface-800 rounded-full overflow-hidden cursor-pointer group">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-brand-500 to-accent-cyan rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
          <input
            type="range"
            min={0}
            max={duration || 0}
            value={currentTime}
            onChange={handleSeek}
            step={0.1}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          {/* Seek indicator */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ left: `calc(${progress}% - 6px)` }}
          />
        </div>
        <div className="flex justify-between mt-1.5">
          <span className="text-xs text-surface-500 font-mono">{formatTime(currentTime)}</span>
          <span className="text-xs text-surface-500 font-mono">{formatTime(duration)}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button onClick={skipBackward} className="btn-ghost p-2 rounded-lg" title="Back 10s">
            <SkipBack className="w-4 h-4" />
          </button>
          <button
            id="play-pause-button"
            onClick={togglePlay}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-lg shadow-brand-600/25 hover:shadow-brand-500/40 transition-shadow active:scale-95"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>
          <button onClick={skipForward} className="btn-ghost p-2 rounded-lg" title="Forward 10s">
            <SkipForward className="w-4 h-4" />
          </button>
        </div>

        {/* Volume */}
        <div className="flex items-center gap-2">
          <button onClick={toggleMute} className="btn-ghost p-2 rounded-lg">
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 h-1 bg-surface-700 rounded-full appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-brand-400 cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
}
