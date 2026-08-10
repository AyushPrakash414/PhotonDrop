import { FileMetadata, SenderState } from '../types/sender';
import { ReceiverState } from '../types/receiver';
import { AppSettings, ActivityRecord } from '../types/transfer';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function selectSenderFile(file: File): Promise<{ status: string; metadata: FileMetadata }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/sender/select-file`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'File selection failed');
  }
  return res.json();
}

export async function selectSenderLocalPath(path: string): Promise<{ status: string; metadata: FileMetadata }> {
  const res = await fetch(`${API_BASE}/api/sender/select-local-path`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Local path selection failed');
  }
  return res.json();
}

export async function startSender(targetFps = 30): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/sender/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_fps: targetFps }),
  });
  return res.json();
}

export async function stopSender(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/sender/stop`, { method: 'POST' });
  return res.json();
}

export async function startReceiver(cameraIndex = 0): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/receiver/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ camera_index: cameraIndex }),
  });
  return res.json();
}

export async function stopReceiver(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/receiver/stop`, { method: 'POST' });
  return res.json();
}

export async function resetReceiver(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/receiver/reset`, { method: 'POST' });
  return res.json();
}

export async function getSettings(): Promise<AppSettings> {
  const res = await fetch(`${API_BASE}/api/settings`);
  return res.json();
}

export async function updateSettings(settings: Partial<AppSettings>): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  return res.json();
}

export async function getActivityHistory(): Promise<ActivityRecord[]> {
  const res = await fetch(`${API_BASE}/api/activity`);
  return res.json();
}
