import { FileMetadata } from './sender';

export type ReceiverStatus =
  | 'IDLE'
  | 'SEARCHING'
  | 'SESSION_DETECTED'
  | 'RECEIVING_METADATA'
  | 'RECEIVING_DATA'
  | 'DECODING'
  | 'RECONSTRUCTING'
  | 'VERIFYING'
  | 'COMPLETE'
  | 'ERROR';

export interface ReceiverStats {
  total_frames: number;
  new_frames: number;
  duplicate_frames: number;
  invalid_frames: number;
  unique_symbols: number;
  payload_bytes: number;
  capture_fps: number;
  decode_fps: number;
  goodput_kbs: number;
  elapsed_time: number;
}

export interface ReceiverTelemetry {
  state: ReceiverStatus;
  progress: number;
  file_name?: string | null;
  file_size?: number | null;
  total_blocks?: number | null;
  sha256?: string | null;
  payload_bytes?: number;
  capture_fps: number;
  decode_fps: number;
  goodput_kbs: number;
  unique_symbols: number;
  duplicates: number;
  invalid: number;
  elapsed_time: number;
}

export interface ReceiverState {
  is_active: boolean;
  frame_b64?: string | null;
  data?: ReceiverTelemetry | null;
}
