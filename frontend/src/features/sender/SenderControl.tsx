import React, { useRef } from 'react';
import { Upload, Play, Square, FileUp } from 'lucide-react';
import { FileMetadata } from '../../types/sender';
import { FileCard } from '../../components/FileCard';
import './SenderControl.css';

interface SenderControlProps {
  metadata: FileMetadata | null;
  isTransmitting: boolean;
  loading: boolean;
  onSelectFile: (file: File) => void;
  onStart: () => void;
  onStop: () => void;
}

export const SenderControl: React.FC<SenderControlProps> = ({
  metadata,
  isTransmitting,
  loading,
  onSelectFile,
  onStart,
  onStop,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onSelectFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="sender-control-container">
      {!metadata ? (
        <div
          className="card dropzone-card"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && onSelectFile(e.target.files[0])}
          />
          <div className="dropzone-icon">
            <Upload size={32} color="var(--accent-primary)" />
          </div>
          <h3>Select a file to transmit</h3>
          <p>Drop your file here or choose from your computer</p>
          <button className="btn-primary" disabled={loading}>
            <FileUp size={18} />
            <span>{loading ? 'Processing...' : 'Select File'}</span>
          </button>
        </div>
      ) : (
        <div className="selected-file-wrapper">
          <FileCard metadata={metadata} onChangeFile={() => fileInputRef.current?.click()} />
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && onSelectFile(e.target.files[0])}
          />

          <div className="action-row">
            {!isTransmitting ? (
              <button className="btn-primary start-btn" onClick={onStart}>
                <Play size={20} />
                <span>START TRANSMISSION</span>
              </button>
            ) : (
              <button className="btn-primary stop-btn" onClick={onStop}>
                <Square size={20} />
                <span>STOP TRANSMISSION</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
