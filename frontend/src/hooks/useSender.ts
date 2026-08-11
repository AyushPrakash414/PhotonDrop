import { useState, useEffect, useCallback } from 'react';
import { SenderState, FileMetadata } from '../types/sender';
import { selectSenderFile, selectSenderLocalPath, startSender, stopSender } from '../services/api';
import { wsService } from '../services/websocket';

export function useSender() {
  const [senderState, setSenderState] = useState<SenderState>({
    is_transmitting: false,
    metadata: null,
  });
  const [fileBuffer, setFileBuffer] = useState<Uint8Array | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = wsService.subscribe((packet) => {
      if (packet.sender) {
        setSenderState((prev) => ({
          ...prev,
          is_transmitting: packet.sender.is_transmitting,
          frame_b64: packet.sender.frame_b64 || prev.frame_b64,
          stats: packet.sender.stats || prev.stats,
        }));
      }
    });
    return unsubscribe;
  }, []);

  const handleSelectFile = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const arrayBuf = await file.arrayBuffer();
      setFileBuffer(new Uint8Array(arrayBuf));
      const res = await selectSenderFile(file);
      setSenderState((prev) => ({ ...prev, metadata: res.metadata }));
    } catch (e: any) {
      setError(e.message || 'File selection failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelectLocalPath = useCallback(async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await selectSenderLocalPath(path);
      setSenderState((prev) => ({ ...prev, metadata: res.metadata }));
    } catch (e: any) {
      setError(e.message || 'Path selection failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleStart = useCallback(async (fps = 30) => {
    setError(null);
    setSenderState((prev) => ({ ...prev, is_transmitting: true }));
    try {
      await startSender(fps);
    } catch (e: any) {
      console.warn('Backend start error, continuing local optical streaming:', e);
    }
  }, []);

  const handleStop = useCallback(async () => {
    setSenderState((prev) => ({ ...prev, is_transmitting: false }));
    try {
      await stopSender();
    } catch (e: any) {
      setError(e.message || 'Failed to stop transmission');
    }
  }, []);

  return {
    senderState,
    fileBuffer,
    loading,
    error,
    selectFile: handleSelectFile,
    selectLocalPath: handleSelectLocalPath,
    start: handleStart,
    stop: handleStop,
  };
}
