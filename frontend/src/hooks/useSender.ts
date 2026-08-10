import { useState, useEffect, useCallback } from 'react';
import { SenderState, FileMetadata } from '../types/sender';
import { selectSenderFile, selectSenderLocalPath, startSender, stopSender } from '../services/api';
import { wsService } from '../services/websocket';

export function useSender() {
  const [senderState, setSenderState] = useState<SenderState>({
    is_transmitting: false,
    metadata: null,
  });
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
    try {
      await startSender(fps);
    } catch (e: any) {
      setError(e.message || 'Failed to start transmission');
    }
  }, []);

  const handleStop = useCallback(async () => {
    try {
      await stopSender();
    } catch (e: any) {
      setError(e.message || 'Failed to stop transmission');
    }
  }, []);

  return {
    senderState,
    loading,
    error,
    selectFile: handleSelectFile,
    selectLocalPath: handleSelectLocalPath,
    start: handleStart,
    stop: handleStop,
  };
}
