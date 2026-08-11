import React, { useEffect, useRef } from 'react';
import QRCode from 'qrcode';
import { SignalIndicator } from '../../components/SignalIndicator';
import {
  buildDataFrame,
  buildManifestFrame,
  encodeSymbol,
  splitIntoChunks,
  Manifest,
} from '../../services/codec';
import { FileMetadata } from '../../types/sender';
import './QRViewer.css';

interface QRViewerProps {
  isTransmitting: boolean;
  frameB64?: string | null;
  file?: File | null;
  fileBuffer?: Uint8Array | null;
  metadata?: FileMetadata | null;
  fps?: number;
}

export const QRViewer: React.FC<QRViewerProps> = ({
  isTransmitting,
  frameB64,
  fileBuffer,
  metadata,
  fps = 30,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const framesRef = useRef(0);
  const seedRef = useRef(0);

  // Client-side high-speed canvas optical QR transmission pump matching lightspeed-share-main
  useEffect(() => {
    if (!isTransmitting || !metadata || !fileBuffer) {
      framesRef.current = 0;
      seedRef.current = 0;
      return;
    }

    let cancelled = false;
    let timer: number | undefined;

    const chunkSize = metadata.block_size || 512;
    const chunks = splitIntoChunks(fileBuffer, chunkSize);
    const manifest: Manifest = {
      name: metadata.file_name,
      size: metadata.file_size,
      mime: metadata.mime_type || 'application/octet-stream',
      digest: metadata.sha256,
      chunks: chunks.length,
      chunkSize,
      fileId: typeof metadata.file_id === 'number' ? metadata.file_id : parseInt(String(metadata.file_id), 16) || 12345,
    };
    const fileId = manifest.fileId || 12345;

    const tick = async () => {
      const canvas = canvasRef.current;
      if (cancelled || !canvas) return;

      const index = framesRef.current;
      const text =
        index % 14 === 0
          ? buildManifestFrame(fileId, manifest)
          : buildDataFrame({
              fileId,
              chunks: manifest.chunks,
              chunkSize: manifest.chunkSize,
              size: manifest.size,
              seed: seedRef.current++,
              payload: encodeSymbol(chunks, seedRef.current - 1),
            });

      try {
        await QRCode.toCanvas(canvas, text, {
          errorCorrectionLevel: 'M',
          margin: 2,
          width: 440,
          color: { dark: '#000000ff', light: '#ffffffff' },
        });
      } catch {
        /* frame skipped */
      }

      canvas.style.removeProperty('width');
      canvas.style.removeProperty('height');

      framesRef.current = index + 1;

      if (!cancelled) {
        timer = window.setTimeout(tick, Math.round(1000 / fps));
      }
    };

    void tick();

    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [isTransmitting, metadata, fileBuffer, fps]);

  const showCanvas = isTransmitting && metadata && fileBuffer;

  return (
    <div className="card card-large qr-viewer-card">
      <div className="qr-viewport-container">
        <SignalIndicator active={isTransmitting} />

        <div className={`qr-display-box ${isTransmitting ? 'transmitting' : ''}`}>
          {/* High-speed local Canvas rendering */}
          <canvas
            ref={canvasRef}
            className="qr-canvas-element"
            style={{ display: showCanvas ? 'block' : 'none', width: '100%', maxHeight: '440px', borderRadius: '12px' }}
          />

          {/* Backend Base64 JPEG Fallback if canvas not active */}
          {!showCanvas && frameB64 && (
            <img src={`data:image/png;base64,${frameB64}`} alt="Optical Data Frame" className="qr-frame-img" />
          )}

          {/* Offline Placeholder */}
          {!showCanvas && !frameB64 && (
            <div className="qr-placeholder">
              <div className="placeholder-grid" />
              <span>Optical Data Output</span>
            </div>
          )}
        </div>
      </div>

      <div className="qr-viewer-footer">
        <div className="transmission-status">
          <span className={`status-dot ${isTransmitting ? 'active' : ''}`} />
          <span className="status-text font-mono">
            {isTransmitting ? 'TRANSMITTING CONTINUOUS OPTICAL STREAM' : 'IDLE — READY TO SEND'}
          </span>
        </div>
        <p className="instruction-text">
          Point the receiver camera directly at this visual display screen
        </p>
      </div>
    </div>
  );
};
