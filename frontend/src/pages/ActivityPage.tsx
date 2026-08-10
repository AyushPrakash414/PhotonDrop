import React, { useState, useEffect } from 'react';
import { History, ShieldCheck } from 'lucide-react';
import { ActivityItem } from '../components/ActivityItem';
import { getActivityHistory } from '../services/api';
import { ActivityRecord } from '../types/transfer';
import './ActivityPage.css';

export const ActivityPage: React.FC = () => {
  const [history, setHistory] = useState<ActivityRecord[]>([]);

  useEffect(() => {
    getActivityHistory().then(setHistory).catch(() => {});
  }, []);

  return (
    <div className="activity-page animate-fade-in">
      <div className="activity-header-card card">
        <div className="history-brand font-mono">
          <History size={20} color="var(--accent-primary)" />
          <span>Local Optical Transfer Log</span>
        </div>
        <p>
          Metadata for transfers performed locally on this machine. Files remain stored safely on your device.
        </p>
      </div>

      <div className="activity-list">
        {history.length === 0 ? (
          <div className="card empty-activity">
            <ShieldCheck size={36} color="var(--text-muted)" />
            <p>No recent transfers logged yet.</p>
          </div>
        ) : (
          history.map((item) => <ActivityItem key={item.id} item={item} />)
        )}
      </div>
    </div>
  );
};
