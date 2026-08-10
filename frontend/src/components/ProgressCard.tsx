import React from 'react';
import { formatBytes } from '../services/fileTransfer';
import './ProgressCard.css';

interface ProgressCardProps {
  title?: string;
  progress: number;
  transferredBytes?: number;
  totalBytes?: number;
  subtext?: string;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({
  title = 'Transfer Progress',
  progress,
  transferredBytes,
  totalBytes,
  subtext,
}) => {
  const percentClamped = Math.min(Math.max(progress, 0), 100);

  return (
    <div className="card progress-card">
      <div className="progress-header">
        <span className="progress-title">{title}</span>
        <span className="progress-percent font-mono">{percentClamped.toFixed(1)}%</span>
      </div>

      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${percentClamped}%` }} />
      </div>

      <div className="progress-footer">
        <span className="progress-bytes">
          {transferredBytes !== undefined && totalBytes !== undefined
            ? `${formatBytes(transferredBytes)} / ${formatBytes(totalBytes)}`
            : subtext || ''}
        </span>
      </div>
    </div>
  );
};
