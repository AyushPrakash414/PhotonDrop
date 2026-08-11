import React, { useCallback, useEffect, useRef, useState } from 'react';
import jsQR from 'jsqr';
import {
  Camera,
  CameraOff,
  Video,
  Activity,
  Zap,
  CheckCircle2,
  Copy,
  AlertTriangle,
  Download,
  ShieldCheck,
  ShieldAlert,
  RotateCcw,
} from 'lucide-react';
import {
  FountainDecoder,
  formatBytes,
  parseFrame,
  sha256Hex,
  Manifest,
} from '../services/codec';
import { MetricCard } from '../components/MetricCard';
import { ProgressCard } from '../components/ProgressCard';
import { CompletionModal } from '../features/receiver/CompletionModal';
import './ReceivePage.css';

type Verification = 'pending' | 'verified' | 'mismatch';

export const ReceivePage: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const decoderRef = useRef<FountainDecoder | null>(null);
  const manifestRef = useRef<Manifest | null>(null);
  const statsRef = useRef({ frames: 0, useful: 0, duplicates: 0, lastTick: 0, decoded: 0 });

  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [solved, setSolved] = useState(0);
  const [stats, setStats] = useState({ frames: 0, useful: 0, duplicates: 0, fps: 0 });
  const [verification, setVerification] = useState<Verification>('pending');
  const [result, setResult] = useState<{ url: string; name: string; size: number } | null>(null);

  const reset = useCallback(() => {
    decoderRef.current = null;
    manifestRef.current = null;
    statsRef.current = { frames: 0, useful: 0, duplicates: 0, lastTick: 0, decoded: 0 };
    setManifest(null);
    setSolved(0);
    setStats({ frames: 0, useful: 0, duplicates: 0, fps: 0 });
    setVerification('pending');
    setResult(null);
    setError(null);
  }, []);

  const finish = useCallback(async (decoder: FountainDecoder, activeManifest: Manifest) => {
    const bytes = decoder.assemble();
    if (!bytes) return;
    const digest = await sha256Hex(bytes);
    const ok = digest === activeManifest.digest;
    setVerification(ok ? 'verified' : 'mismatch');
    const blob = new Blob([bytes.slice().buffer as ArrayBuffer], { type: activeManifest.mime || 'application/octet-stream' });
    setResult({
      url: URL.createObjectURL(blob),
      name: activeManifest.name,
      size: activeManifest.size,
    });
    setScanning(false);
  }, []);

  useEffect(() => {
    if (!scanning) return;
    let cancelled = false;
    let stream: MediaStream | null = null;
    let raf = 0;

    const handleFrame = (text: string) => {
      const frame = parseFrame(text);
      if (!frame) return;
      const s = statsRef.current;
      s.frames += 1;

      const now = performance.now();
      if (now - s.lastTick >= 1000) {
        const fps = (s.decoded * 1000) / (now - s.lastTick);
        s.lastTick = now;
        s.decoded = 0;
        setStats({ frames: s.frames, useful: s.useful, duplicates: s.duplicates, fps });
      }
      s.decoded += 1;

      if (frame.type === 'manifest') {
        if (!manifestRef.current) {
          manifestRef.current = frame.manifest;
          setManifest(frame.manifest);
          decoderRef.current = new FountainDecoder(
            frame.manifest.chunks,
            frame.manifest.chunkSize,
            frame.manifest.size,
          );
        }
        return;
      }

      if (!decoderRef.current) {
        decoderRef.current = new FountainDecoder(frame.chunks, frame.chunkSize, frame.size);
      }
      const decoder = decoderRef.current;
      if (decoder.chunks !== frame.chunks) return;
      if (decoder.hasSeed(frame.seed)) {
        s.duplicates += 1;
        return;
      }
      if (decoder.addSymbol(frame.seed, frame.payload)) {
        s.useful += 1;
      }
      setSolved(decoder.solvedCount);
      setStats({ frames: s.frames, useful: s.useful, duplicates: s.duplicates, fps: s.decoded });

      if (decoder.complete && manifestRef.current) {
        void finish(decoder, manifestRef.current);
      }
    };

    const start = async () => {
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error('Camera requires HTTPS or localhost in browser');
        }
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
        });
      } catch (err: any) {
        setError(err.message || 'Camera access was denied. Allow camera permission to receive optical frames.');
        setScanning(false);
        return;
      }
      const video = videoRef.current;
      if (!video || cancelled) return;
      video.srcObject = stream;
      await video.play().catch(() => undefined);

      const loop = () => {
        if (cancelled) return;
        const canvas = canvasRef.current;
        const context = canvas?.getContext('2d', { willReadFrequently: true });
        if (canvas && context && video.readyState >= 2 && video.videoWidth) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          const image = context.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(image.data, image.width, image.height, {
            inversionAttempts: 'dontInvert',
          });
          if (code?.data) handleFrame(code.data);
        }
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);
    };

    void start();

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [scanning, finish]);

  const total = manifest?.chunks ?? 0;
  const progress = total ? Math.min(100, (solved / total) * 100) : 0;
  const isComplete = verification === 'verified';
  const isError = verification === 'mismatch';

  return (
    <div className="receive-page animate-fade-in">
      {error && <div className="error-alert">{error}</div>}

      <div className="receive-header-row">
        <div className="receive-status-box">
          <span className={`status-dot ${scanning ? 'active' : ''}`} />
          <span className="font-mono text-sm font-semibold">
            {scanning ? 'CAMERA ACTIVE — SCANNING OPTICAL FRAMES' : 'RECEIVER IDLE'}
          </span>
        </div>

        <div className="control-btn-group">
          <button
            type="button"
            onClick={() => {
              if (scanning) {
                setScanning(false);
                return;
              }
              reset();
              setScanning(true);
            }}
            className={`btn ${scanning ? 'btn-danger' : 'btn-primary'}`}
          >
            <Video size={18} />
            <span>{scanning ? 'Stop Capture' : 'Start Capture'}</span>
          </button>

          <button type="button" onClick={reset} className="btn btn-secondary">
            <RotateCcw size={18} />
            <span>Reset Decoder</span>
          </button>
        </div>
      </div>

      <div className="receive-layout">
        {/* Left Column: Camera Viewport */}
        <div className="receive-col-left">
          <div className="card card-large camera-viewer-card">
            <div className="camera-viewport">
              <video
                ref={videoRef}
                playsInline
                muted
                className={`camera-feed-video ${scanning ? 'visible' : 'hidden'}`}
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />

              {!scanning && (
                <div className="camera-placeholder">
                  <CameraOff size={48} color="var(--text-muted)" />
                  <span>Camera idle — Click Start Capture to lock onto sender screen</span>
                </div>
              )}

              {scanning && (
                <div className="detection-overlay detected">
                  <div className="target-finder-box">
                    <div className="finder-corner top-left" />
                    <div className="finder-corner top-right" />
                    <div className="finder-corner bottom-left" />
                    <div className="finder-corner bottom-right" />
                  </div>
                  <span className="detection-badge">SCANNING FOR QR</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Progress & Metrics */}
        <div className="receive-col-right">
          {manifest && (
            <div className="card receive-file-card">
              <h3>Receiving: {manifest.name}</h3>
              <span>{formatBytes(manifest.size)}</span>
            </div>
          )}

          <ProgressCard
            title="Decoding Progress"
            progress={progress}
            subtext={
              manifest
                ? `Chunks recovered ${solved} / ${total}`
                : 'Waiting for manifest frame from sender...'
            }
          />

          <div className="metrics-grid-3">
            <MetricCard label="Frames Seen" value={stats.frames} icon={<Camera size={16} />} />
            <MetricCard label="Useful" value={stats.useful} icon={<CheckCircle2 size={16} />} />
            <MetricCard label="Duplicates" value={stats.duplicates} icon={<Copy size={16} />} />
            <MetricCard label="Decode FPS" value={stats.fps.toFixed(1)} icon={<Activity size={16} />} accent />
          </div>

          {verification !== 'pending' && (
            <div className={`verification-badge-card ${verification}`}>
              {verification === 'verified' ? (
                <ShieldCheck size={20} color="var(--success)" />
              ) : (
                <ShieldAlert size={20} color="var(--error)" />
              )}
              <span>
                {verification === 'verified'
                  ? 'SHA-256 integrity verified — file is 100% byte-identical!'
                  : 'Digest mismatch — data corrupted, rescan required.'}
              </span>
            </div>
          )}

          {result && (
            <a
              href={result.url}
              download={result.name}
              className="btn btn-success btn-large mt-4"
              style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              <Download size={20} />
              <span>Save {result.name} ({formatBytes(result.size)})</span>
            </a>
          )}
        </div>
      </div>

      {/* Completion Modal */}
      <CompletionModal
        isComplete={isComplete}
        isError={isError}
        fileName={manifest?.name}
        fileSize={manifest?.size}
        sha256={manifest?.digest}
        onReset={reset}
      />
    </div>
  );
};
