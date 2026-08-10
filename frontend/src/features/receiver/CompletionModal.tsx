import React from 'react';
import { CheckCircle, AlertTriangle, FileCheck, FolderOpen } from 'lucide-react';
import { formatBytes, shortenHash } from '../../services/fileTransfer';
import './CompletionModal.css';

interface CompletionModalProps {
  isComplete: boolean;
  isError: boolean;
  fileName?: string | null;
  fileSize?: number | null;
  sha256?: string | null;
  onReset: () => void;
}

export const CompletionModal: React.FC<CompletionModalProps> = ({
  isComplete,
  isError,
  fileName,
  fileSize,
  sha256,
  onReset,
}) => {
  if (!isComplete && !isError) return null;

  return (
    <div className="modal-backdrop">
      <div className={`card card-large completion-card ${isError ? 'error-card' : ''}`}>
        <div className="completion-icon">
          {isComplete ? (
            <CheckCircle size={48} color="var(--success)" />
          ) : (
            <AlertTriangle size={48} color="var(--error)" />
          )}
        </div>

        <h2 className="completion-title">
          {isComplete ? 'Transfer Complete' : 'Transfer Failed'}
        </h2>

        <p className="completion-subtitle">
          {isComplete
            ? 'Original file successfully reconstructed and verified'
            : 'File integrity verification failed or corrupted packet received'}
        </p>

        {fileName && (
          <div className="reconstructed-file-box">
            <div className="file-info-header">
              <FileCheck size={20} color="var(--success)" />
              <span className="rec-name">{fileName}</span>
            </div>
            {fileSize && <span className="rec-size">{formatBytes(fileSize)}</span>}
            {sha256 && (
              <div className="hash-verify-row">
                <span>SHA-256 Verified ✓</span>
                <span className="hash-code font-mono">{shortenHash(sha256, 12)}</span>
              </div>
            )}
          </div>
        )}

        <div className="completion-actions">
          {isComplete ? (
            <button className="btn-primary" onClick={onReset}>
              <FolderOpen size={18} />
              <span>Done / Open Output</span>
            </button>
          ) : (
            <button className="btn-primary error-retry-btn" onClick={onReset}>
              <span>Try Again</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
