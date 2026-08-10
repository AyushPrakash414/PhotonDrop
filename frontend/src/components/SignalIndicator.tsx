import React from 'react';
import './SignalIndicator.css';

interface SignalIndicatorProps {
  active: boolean;
}

export const SignalIndicator: React.FC<SignalIndicatorProps> = ({ active }) => {
  return (
    <div className={`signal-container ${active ? 'active' : ''}`}>
      <div className="ring ring-outer animate-pulse-rings" />
      <div className="ring ring-middle" />
      <div className="ring ring-inner" />
      <div className="signal-core" />
    </div>
  );
};
