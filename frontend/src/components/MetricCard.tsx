import React from 'react';
import './MetricCard.css';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  accent?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, unit, icon, accent }) => {
  return (
    <div className={`metric-card ${accent ? 'metric-accent' : ''}`}>
      <div className="metric-header">
        <span className="metric-label">{label}</span>
        {icon && <div className="metric-icon">{icon}</div>}
      </div>
      <div className="metric-body">
        <span className="metric-value">{value}</span>
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
    </div>
  );
};
