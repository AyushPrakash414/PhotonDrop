import React from 'react';
import { Activity, Zap, Layers, Hash } from 'lucide-react';
import { useSender } from '../hooks/useSender';
import { SenderControl } from '../features/sender/SenderControl';
import { QRViewer } from '../features/sender/QRViewer';
import { MetricCard } from '../components/MetricCard';
import { ProgressCard } from '../components/ProgressCard';
import { shortenHash } from '../services/fileTransfer';
import './SendPage.css';

export const SendPage: React.FC = () => {
  const { senderState, fileBuffer, loading, error, selectFile, start, stop } = useSender();

  const metadata = senderState.metadata;
  const isTransmitting = senderState.is_transmitting;
  const stats = senderState.stats;

  return (
    <div className="send-page animate-fade-in">
      {error && <div className="error-alert">{error}</div>}

      <div className="send-layout">
        {/* Left Column: Control & Metadata */}
        <div className="send-col-left">
          <SenderControl
            metadata={metadata}
            isTransmitting={isTransmitting}
            loading={loading}
            onSelectFile={selectFile}
            onStart={() => start(30)}
            onStop={stop}
          />

          {metadata && isTransmitting && (
            <ProgressCard
              title="Transmission Output"
              progress={100}
              subtext={`Continuous Fountain Stream · ${metadata.total_source_blocks} source blocks`}
            />
          )}

          {metadata && (
            <div className="metrics-grid-2">
              <MetricCard
                label="Display FPS"
                value={stats?.display_fps || (isTransmitting ? '30.0' : '0.0')}
                unit="FPS"
                icon={<Activity size={18} />}
              />
              <MetricCard
                label="Goodput"
                value={stats?.goodput_kbs || (isTransmitting ? '15.0' : '0.0')}
                unit="KB/s"
                icon={<Zap size={18} />}
                accent
              />
              <MetricCard
                label="Symbols"
                value={stats?.symbols || 0}
                icon={<Layers size={18} />}
              />
              <MetricCard
                label="Session"
                value={shortenHash(String(metadata.session_id || metadata.file_id), 4)}
                icon={<Hash size={18} />}
              />
            </div>
          )}
        </div>

        {/* Right Column: Visual QR Viewer */}
        <div className="send-col-right">
          <QRViewer
            isTransmitting={isTransmitting}
            frameB64={senderState.frame_b64}
            fileBuffer={fileBuffer}
            metadata={metadata}
            fps={30}
          />
        </div>
      </div>
    </div>
  );
};
