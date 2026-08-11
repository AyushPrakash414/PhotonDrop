import { useState, useEffect, useCallback } from 'react';
import { ReceiverState } from '../types/receiver';
import { startReceiver, stopReceiver, resetReceiver } from '../services/api';
import { wsService } from '../services/websocket';

export function useReceiver() {
  const [receiverState, setReceiverState] = useState<ReceiverState>({
    is_active: false,
    data: null,
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = wsService.subscribe((packet) => {
      if (packet.receiver) {
        setReceiverState((prev) => ({
          ...prev,
          is_active: packet.receiver.is_active,
          frame_b64: packet.receiver.frame_b64 || prev.frame_b64,
          data: packet.receiver.data || prev.data,
        }));
      }
    });
    return unsubscribe;
  }, []);

  const handleStart = useCallback(async (cameraIndex = 0) => {
    setError(null);
    try {
      await startReceiver(cameraIndex, 'browser');
    } catch (e: any) {
      setError(e.message || 'Failed to start camera');
    }
  }, []);

  const handleStop = useCallback(async () => {
    try {
      await stopReceiver();
    } catch (e: any) {
      setError(e.message || 'Failed to stop camera');
    }
  }, []);

  const handleReset = useCallback(async () => {
    try {
      await resetReceiver();
    } catch (e: any) {
      setError(e.message || 'Failed to reset receiver');
    }
  }, []);

  return {
    receiverState,
    error,
    start: handleStart,
    stop: handleStop,
    reset: handleReset,
  };
}
