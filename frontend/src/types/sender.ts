export interface FileMetadata {
  file_id: string;
  session_id: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  block_size: number;
  total_source_blocks: number;
  sha256: string;
}

export interface SenderStats {
  display_fps: number;
  goodput_kbs: number;
  symbols: number;
  elapsed_time: number;
}

export interface SenderState {
  is_transmitting: boolean;
  metadata: FileMetadata | null;
  frame_b64?: string | null;
  stats?: SenderStats | null;
}
