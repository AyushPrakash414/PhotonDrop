import React from 'react';
import { SignalIndicator } from '../../components/SignalIndicator';
import './QRViewer.css';

interface QRViewerProps {
  isTransmitting: boolean;
  frameB64?: string | null;
}

export const QRViewer: React.FC<QRViewerProps> = ({ isTransmitting, frameB64 }) => {
  return (
    <div className="card card-large qr-viewer-card">
      <div className="qr-viewport-container">
        <SignalIndicator active={isTransmitting} />

        <div className={`qr-display-box ${isTransmitting ? 'transmitting' : ''}`}>
          {frameB64 ? (
            <img src={`data:image/png;base64,${frameB64}`} alt="Optical Data Frame" className="qr-frame-img" />
          ) : (
            <div className="qr-placeholder">
              <div className="placeholder-grid" />
              <span>Optical Data Output</span>
            </div>
          )}
        </div>
      </div>

      <div className="qr-viewer-footer">
        <div className="transmission-status">
          <span className={`status-dot ${isTransmitting ? 'active' : ''}`} />
          <span className="status-text">
            {isTransmitting ? 'TRANSMITTING' : 'IDLE — READY TO SEND'}
          </span>
        </div>
        <p className="instruction-text">
          Point the receiver camera directly at this visual display screen
        </p>
      </div>
    </div>
  );
};
