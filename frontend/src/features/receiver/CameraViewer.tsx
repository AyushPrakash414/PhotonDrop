import React from 'react';
import { Camera, Eye } from 'lucide-react';
import { ReceiverStatus } from '../../types/receiver';
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
  const isDetected = status && ['RECEIVING_DATA', 'DECODING', 'RECONSTRUCTING', 'VERIFYING', 'COMPLETE'].includes(status);

  return (
    <div className="card card-large camera-viewer-card">
      <div className="camera-viewport">
        {frameB64 ? (
          <img src={`data:image/jpeg;base64,${frameB64}`} alt="Camera Preview" className="camera-feed-img" />
        ) : (
          <div className="camera-placeholder">
            <Camera size={48} color="var(--text-muted)" />
            <span>{isActive ? 'Initializing camera feed...' : 'Camera Off — Click Start Receiving'}</span>
          </div>
        )}

        {isActive && isDetected && (
          <div className="detection-overlay">
            <div className="detection-box">
              <span className="detection-badge">DATA DETECTED</span>
            </div>
          </div>
        )}
      </div>

      <div className="camera-viewer-footer">
        <div className="signal-status font-mono">
          <Eye size={16} color={isActive ? 'var(--success)' : 'var(--text-muted)'} />
          <span>{isActive ? 'SCANNING OPTICAL CHANNEL' : 'OFFLINE'}</span>
        </div>
      </div>
    </div>
  );
};
