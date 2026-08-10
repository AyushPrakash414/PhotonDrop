import { SenderState } from '../types/sender';
import { ReceiverState } from '../types/receiver';

export interface TelemetryPacket {
  type: 'telemetry';
  sender: SenderState;
  receiver: ReceiverState;
}

type TelemetryCallback = (data: TelemetryPacket) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Set<TelemetryCallback> = new Set();
  private reconnectTimer: number | null = null;
  private isConnected = false;

  public connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const wsOverride = import.meta.env.VITE_WS_BASE_URL;
    let wsUrl: string;
    if (wsOverride) {
      wsUrl = `${wsOverride.replace(/\/$/, '')}/ws`;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}/ws`;
    }

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const packet: TelemetryPacket = JSON.parse(event.data);
          this.listeners.forEach((cb) => cb(packet));
        } catch (e) {
          console.error('Failed to parse WebSocket packet', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.isConnected = false;
        this.ws?.close();
      };
    } catch (e) {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = window.setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 2000);
    }
  }

  public subscribe(callback: TelemetryCallback): () => void {
    this.listeners.add(callback);
    this.connect();
    return () => {
      this.listeners.delete(callback);
    };
  }

  public getConnectedStatus(): boolean {
    return this.isConnected;
  }
}

export const wsService = new WebSocketService();
