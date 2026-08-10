import React, { useEffect, useRef, useState } from 'react';
import { Camera, Eye, SwitchCamera } from 'lucide-react';
import { ReceiverStatus } from '../../types/receiver';
import { sendReceiverFrame } from '../../services/api';
import './CameraViewer.css';

interface CameraViewerProps {
  isActive: boolean;
  frameB64?: string | null;
  status?: ReceiverStatus;
}

export const CameraViewer: React.FC<CameraViewerProps> = ({
  isActive,
  frameB64,
  status,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');
  const [hasWebcamAccess, setHasWebcamAccess] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const isDetected = status && ['RECEIVING_DATA', 'DECODING', 'RECONSTRUCTING', 'VERIFYING', 'COMPLETE'].includes(status);

  // Initialize browser/mobile camera stream using getUserMedia
  useEffect(() => {
    let stream: MediaStream | null = null;
    let frameInterval: number | null = null;

    if (isActive) {
      const startWebCamera = async () => {
        try {
          setCameraError(null);
          stream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: { ideal: facingMode },
              width: { ideal: 1280 },
              height: { ideal: 720 },
            },
          });

          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            await videoRef.current.play();
            setHasWebcamAccess(true);
          }

          // Capture frames at ~10 FPS and transmit to Python receiver pipeline
          frameInterval = window.setInterval(() => {
            if (videoRef.current && canvasRef.current && videoRef.current.readyState === 4) {
              const video = videoRef.current;
              const canvas = canvasRef.current;
              const ctx = canvas.getContext('2d');
              if (ctx) {
                const maxDim = 640;
                let w = video.videoWidth || 640;
                let h = video.videoHeight || 480;
                if (Math.max(w, h) > maxDim) {
                  const scale = maxDim / Math.max(w, h);
                  w = Math.round(w * scale);
                  h = Math.round(h * scale);
                }
                canvas.width = w;
                canvas.height = h;
                ctx.drawImage(video, 0, 0, w, h);
                const frameDataUrl = canvas.toDataURL('image/jpeg', 0.8);
                sendReceiverFrame(frameDataUrl).catch(() => {});
              }
            }
          }, 100);
        } catch (err: any) {
          console.warn('Browser webcam access failed, falling back to server camera stream:', err);
          setHasWebcamAccess(false);
          setCameraError(err.message || 'Camera access denied');
        }
      };

      startWebCamera();
    } else {
      setHasWebcamAccess(false);
      setCameraError(null);
    }

    return () => {
      if (frameInterval) clearInterval(frameInterval);
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [isActive, facingMode]);

  const toggleCameraFacing = () => {
    setFacingMode((prev) => (prev === 'environment' ? 'user' : 'environment'));
  };

  return (
    <div className="card card-large camera-viewer-card">
      <div className="camera-viewport">
        {/* Hidden Canvas for frame processing */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* HTML5 Live Video Element for Mobile/Web Browser Camera */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`camera-feed-video ${isActive && hasWebcamAccess ? 'visible' : 'hidden'}`}
        />

        {/* Backend OpenCV Stream Fallback */}
        {!hasWebcamAccess && frameB64 && (
          <img src={`data:image/jpeg;base64,${frameB64}`} alt="Camera Preview" className="camera-feed-img" />
        )}

        {/* Offline Placeholder */}
        {!hasWebcamAccess && !frameB64 && (
          <div className="camera-placeholder">
            <Camera size={48} color="var(--text-muted)" />
            <span>{isActive ? 'Initializing camera...' : 'Camera Off — Click Start Receiving'}</span>
            {cameraError && <span className="camera-error-msg">{cameraError}</span>}
          </div>
        )}

        {/* Optical Alignment Target Overlay */}
        {isActive && (
          <div className={`detection-overlay ${isDetected ? 'detected' : ''}`}>
            <div className="target-finder-box">
              <div className="finder-corner top-left" />
              <div className="finder-corner top-right" />
              <div className="finder-corner bottom-left" />
              <div className="finder-corner bottom-right" />
            </div>
            {isDetected && <span className="detection-badge">DATA DETECTED</span>}
          </div>
        )}
      </div>

      <div className="camera-viewer-footer">
        <div className="signal-status font-mono">
          <Eye size={16} color={isActive ? 'var(--success)' : 'var(--text-muted)'} />
          <span>{isActive ? (hasWebcamAccess ? 'MOBILE CAMERA SCANNING' : 'SERVER CAMERA SCANNING') : 'OFFLINE'}</span>
        </div>

        {isActive && hasWebcamAccess && (
          <button className="camera-switch-btn" onClick={toggleCameraFacing} title="Switch Front/Back Camera">
            <SwitchCamera size={16} />
            <span>{facingMode === 'environment' ? 'Back Cam' : 'Front Cam'}</span>
          </button>
        )}
      </div>
    </div>
  );
};
