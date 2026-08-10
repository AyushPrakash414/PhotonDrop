import React from 'react';
import { ReceiverStatus } from '../types/receiver';
import './StatusBadge.css';

interface StatusBadgeProps {
  status: ReceiverStatus | 'TRANSMITTING' | 'RECEIVING' | 'IDLE';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  let badgeClass = 'status-idle';
  let label = status as string;

  switch (status) {
    case 'SEARCHING':
      badgeClass = 'status-warning';
      label = '● SEARCHING';
      break;
    case 'SESSION_DETECTED':
    case 'RECEIVING_METADATA':
    case 'RECEIVING_DATA':
    case 'RECEIVING':
      badgeClass = 'status-active';
      label = '● RECEIVING';
      break;
    case 'TRANSMITTING':
      badgeClass = 'status-active';
      label = '● TRANSMITTING';
      break;
    case 'DECODING':
    case 'RECONSTRUCTING':
      badgeClass = 'status-active';
      label = '● DECODING';
      break;
    case 'VERIFYING':
      badgeClass = 'status-warning';
      label = '● VERIFYING SHA-256';
      break;
    case 'COMPLETE':
      badgeClass = 'status-success';
      label = '✓ TRANSFER COMPLETE';
      break;
    case 'ERROR':
      badgeClass = 'status-error';
      label = '! INTEGRITY ERROR';
      break;
    default:
      badgeClass = 'status-idle';
      label = '● IDLE';
      break;
  }

  return <div className={`status-badge ${badgeClass}`}>{label}</div>;
};
