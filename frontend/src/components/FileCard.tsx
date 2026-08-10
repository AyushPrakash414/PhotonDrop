import React from 'react';
import { FileText, CheckCircle, RefreshCw } from 'lucide-react';
import { FileMetadata } from '../types/sender';
import { formatBytes, shortenHash } from '../services/fileTransfer';
import './FileCard.css';

interface FileCardProps {
  metadata: FileMetadata;
  onChangeFile?: () => void;
}

export const FileCard: React.FC<FileCardProps> = ({ metadata, onChangeFile }) => {
  return (
    <div className="card file-card">
      <div className="file-header">
        <div className="file-icon-box">
          <FileText size={24} color="var(--accent-primary)" />
        </div>
        <div className="file-details">
          <h3 className="file-name">{metadata.file_name}</h3>
          <span className="file-meta">
            {formatBytes(metadata.file_size)} · {metadata.total_source_blocks} blocks · {metadata.mime_type}
          </span>
        </div>
        {onChangeFile && (
          <button className="btn-secondary change-btn" onClick={onChangeFile}>
            <RefreshCw size={14} />
            <span>Change File</span>
          </button>
        )}
      </div>

      <div className="hash-box">
        <span className="hash-title">SHA-256</span>
        <span className="hash-value font-mono">{metadata.sha256}</span>
      </div>
    </div>
  );
};
