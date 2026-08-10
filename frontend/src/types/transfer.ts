export interface ActivityRecord {
  id: string;
  type: 'sent' | 'received';
  fileName: string;
  fileSize: number;
  durationSeconds: number;
  verified: boolean;
  timestamp: string;
  sha256?: string;
}

export interface AppSettings {
  camera_resolution: string;
  target_camera_fps: number;
  target_sender_fps: number;
  qr_error_correction: string;
  download_path: string;
  theme: 'light' | 'dark' | 'system';
}
