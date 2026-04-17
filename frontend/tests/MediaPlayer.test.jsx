import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import MediaPlayer from '../src/components/MediaPlayer';

describe('MediaPlayer', () => {
  const videoDocument = {
    id: 'doc-1',
    filename: 'test_video.mp4',
    original_filename: 'my_video.mp4',
    file_type: 'video',
    duration_seconds: 120,
  };

  const audioDocument = {
    id: 'doc-2',
    filename: 'test_audio.mp3',
    original_filename: 'my_audio.mp3',
    file_type: 'audio',
    duration_seconds: 60,
  };

  it('renders video player for video documents', () => {
    render(<MediaPlayer document={videoDocument} seekTo={0} />);
    expect(screen.getByText(/Media Player/)).toBeInTheDocument();
  });

  it('renders audio player for audio documents', () => {
    render(<MediaPlayer document={audioDocument} seekTo={0} />);
    expect(screen.getByText(/Media Player/)).toBeInTheDocument();
  });

  it('shows play/pause button', () => {
    render(<MediaPlayer document={videoDocument} seekTo={0} />);
    const playButton = document.getElementById('play-pause-button');
    expect(playButton).toBeInTheDocument();
  });

  it('renders time display', () => {
    render(<MediaPlayer document={videoDocument} seekTo={0} />);
    const timeDisplays = screen.getAllByText('0:00');
    expect(timeDisplays.length).toBeGreaterThanOrEqual(1);
  });

  it('renders volume controls', () => {
    render(<MediaPlayer document={videoDocument} seekTo={0} />);
    const rangeInputs = screen.getAllByRole('slider');
    expect(rangeInputs.length).toBeGreaterThanOrEqual(1);
  });

  it('returns null when no document provided', () => {
    const { container } = render(<MediaPlayer document={null} seekTo={0} />);
    expect(container.innerHTML).toBe('');
  });

  it('returns null when document has no filename', () => {
    const { container } = render(
      <MediaPlayer document={{ ...videoDocument, filename: null }} seekTo={0} />
    );
    expect(container.innerHTML).toBe('');
  });

  it('renders skip controls', () => {
    render(<MediaPlayer document={videoDocument} seekTo={0} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(3);
  });

  it('creates video element for video type', () => {
    render(<MediaPlayer document={videoDocument} seekTo={0} />);
    const videoElement = document.querySelector('video');
    expect(videoElement).toBeInTheDocument();
    expect(videoElement.src).toContain('test_video.mp4');
  });

  it('creates audio element for audio type', () => {
    render(<MediaPlayer document={audioDocument} seekTo={0} />);
    const audioElement = document.querySelector('audio');
    expect(audioElement).toBeInTheDocument();
    expect(audioElement.src).toContain('test_audio.mp3');
  });

  it('has proper aspect ratio container for video', () => {
    render(<MediaPlayer document={videoDocument} seekTo={0} />);
    const videoContainer = document.querySelector('.aspect-video');
    expect(videoContainer).toBeInTheDocument();
  });
});
