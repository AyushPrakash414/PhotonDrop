import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Download, Zap, Radio, ShieldCheck } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { useSender } from '../hooks/useSender';
import { useReceiver } from '../hooks/useReceiver';
import { formatBytes } from '../services/fileTransfer';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { senderState } = useSender();
  const { receiverState } = useReceiver();

  const isTransmitting = senderState.is_transmitting;
  const isReceiving = receiverState.is_active;

  const currentGoodput =
    (senderState.stats?.goodput_kbs || 0) + (receiverState.data?.goodput_kbs || 0);

  return (
    <div className="dashboard-page animate-fade-in">
      {/* Banner / Intro Card */}
      <div className="card card-large hero-banner">
        <div className="hero-content">
          <span className="hero-pill">Zero-Network Optical Transport</span>
          <h2>Screen-to-Camera Optical Channel</h2>
          <p>
            Transmit arbitrary binary files through visible light using LT fountain coding.
            No Wi-Fi. No Bluetooth. No Internet.
          </p>
          <div className="hero-buttons">
            <button className="btn-primary" onClick={() => navigate('/send')}>
              <Send size={18} />
              <span>Send File</span>
            </button>
            <button className="btn-secondary" onClick={() => navigate('/receive')}>
              <Download size={18} />
              <span>Receive File</span>
            </button>
          </div>
        </div>

        <div className="hero-visual">
          <div className={`optical-ring-core ${isTransmitting || isReceiving ? 'active' : ''}`}>
            <Radio size={42} color="var(--accent-primary)" />
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <MetricCard
          label="Active Goodput"
          value={currentGoodput > 0 ? currentGoodput.toFixed(1) : '0.0'}
          unit="KB/s"
          icon={<Zap size={20} />}
          accent={currentGoodput > 0}
        />
        <MetricCard
          label="Sender FPS"
          value={senderState.stats?.display_fps || '0.0'}
          unit="FPS"
        />
        <MetricCard
          label="Receiver Decode"
          value={receiverState.data?.decode_fps || '0.0'}
          unit="FPS"
        />
        <MetricCard
          label="Optical Link"
          value={isTransmitting ? 'Transmitting' : isReceiving ? 'Receiving' : 'Ready'}
          icon={<ShieldCheck size={20} color="var(--success)" />}
        />
      </div>
    </div>
  );
};
