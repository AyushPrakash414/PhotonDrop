import React from 'react';
import { Camera, Activity, Zap, CheckCircle2, Copy, AlertTriangle } from 'lucide-react';
import { useReceiver } from '../hooks/useReceiver';
import { ReceiverControl } from '../features/receiver/ReceiverControl';
import { CameraViewer } from '../features/receiver/CameraViewer';
import { CompletionModal } from '../features/receiver/CompletionModal';
import { MetricCard } from '../components/MetricCard';
import { ProgressCard } from '../components/ProgressCard';
import { StatusBadge } from '../components/StatusBadge';
import { formatBytes } from '../services/fileTransfer';
import './ReceivePage.css';

export const ReceivePage: React.FC = () => {
  const { receiverState, error, start, stop, reset } = useReceiver();

  const data = receiverState.data;
  const isActive = receiverState.is_active;
  const status = data?.state || 'IDLE';

  const isComplete = status === 'COMPLETE';
  const isError = status === 'ERROR';

  return (
    <div className="receive-page animate-fade-in">
      {error && <div className="error-alert">{error}</div>}

      <div className="receive-header-row">
        <StatusBadge status={status} />
        <ReceiverControl isActive={isActive} onStart={() => start(0)} onStop={stop} onReset={reset} />
      </div>

      <div className="receive-layout">
        {/* Left Column: Camera Viewport */}
        <div className="receive-col-left">
          <CameraViewer isActive={isActive} frameB64={receiverState.frame_b64} status={status} />
        </div>

        {/* Right Column: Progress & Metrics */}
        <div className="receive-col-right">
          {data?.file_name && (
            <div className="card receive-file-card">
              <h3>Receiving: {data.file_name}</h3>
              {data.file_size && <span>{formatBytes(data.file_size)}</span>}
            </div>
          )}

          <ProgressCard
            title="Decoding Progress"
            progress={data?.progress || 0}
            subtext={data?.file_size ? `${formatBytes(data.payload_bytes || 0)} / ${formatBytes(data.file_size)}` : 'Waiting for session metadata...'}
          />

          <div className="metrics-grid-3">
            <MetricCard label="Capture FPS" value={data?.capture_fps || '0'} icon={<Camera size={16} />} />
            <MetricCard label="Decode FPS" value={data?.decode_fps || '0.0'} icon={<Activity size={16} />} />
            <MetricCard label="Goodput" value={data?.goodput_kbs || '0.0'} unit="KB/s" icon={<Zap size={16} />} accent />
            <MetricCard label="Unique" value={data?.unique_symbols || 0} icon={<CheckCircle2 size={16} />} />
            <MetricCard label="Duplicates" value={data?.duplicates || 0} icon={<Copy size={16} />} />
            <MetricCard label="Invalid" value={data?.invalid || 0} icon={<AlertTriangle size={16} />} />
          </div>
        </div>
      </div>

      {/* Completion Modal */}
      <CompletionModal
        isComplete={isComplete}
        isError={isError}
        fileName={data?.file_name}
        fileSize={data?.file_size}
        sha256={data?.sha256}
        onReset={reset}
      />
    </div>
  );
};
