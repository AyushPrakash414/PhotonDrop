import React from 'react';
import { Camera, Square, RotateCcw } from 'lucide-react';
import './ReceiverControl.css';

interface ReceiverControlProps {
  isActive: boolean;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
}

export const ReceiverControl: React.FC<ReceiverControlProps> = ({
  isActive,
  onStart,
  onStop,
  onReset,
}) => {
  return (
    <div className="receiver-control-row">
      {!isActive ? (
        <button className="btn-primary start-camera-btn" onClick={onStart}>
          <Camera size={20} />
          <span>START RECEIVING</span>
        </button>
      ) : (
        <button className="btn-primary stop-camera-btn" onClick={onStop}>
          <Square size={20} />
          <span>STOP CAMERA</span>
        </button>
      )}

      <button className="btn-secondary reset-btn" onClick={onReset}>
        <RotateCcw size={18} />
        <span>Reset</span>
      </button>
    </div>
  );
};
