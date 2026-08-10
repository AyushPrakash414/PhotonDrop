import React from 'react';
import { ArrowUpRight, ArrowDownLeft, CheckCircle2 } from 'lucide-react';
import { ActivityRecord } from '../types/transfer';
import { formatBytes, formatTime } from '../services/fileTransfer';
import './ActivityItem.css';

interface ActivityItemProps {
  item: ActivityRecord;
}

export const ActivityItem: React.FC<ActivityItemProps> = ({ item }) => {
  const isSent = item.type === 'sent';

  return (
    <div className="card activity-item">
      <div className={`activity-icon ${isSent ? 'icon-sent' : 'icon-received'}`}>
        {isSent ? <ArrowUpRight size={20} /> : <ArrowDownLeft size={20} />}
      </div>

      <div className="activity-info">
        <h4 className="activity-name">{item.fileName}</h4>
        <span className="activity-sub">
          {formatBytes(item.fileSize)} · {isSent ? 'Sent' : 'Received'} · {formatTime(item.durationSeconds)}
        </span>
      </div>

      {item.verified && (
        <div className="verified-pill">
          <CheckCircle2 size={14} />
          <span>Verified</span>
        </div>
      )}
    </div>
  );
};
