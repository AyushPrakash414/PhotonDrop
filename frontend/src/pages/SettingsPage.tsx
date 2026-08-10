import React, { useState, useEffect } from 'react';
import { Camera, Sliders, Folder, Sun, Moon, Check } from 'lucide-react';
import { getSettings, updateSettings } from '../services/api';
import { AppSettings } from '../types/transfer';
import './SettingsPage.css';

interface SettingsPageProps {
  currentTheme: 'light' | 'dark' | 'system';
  onThemeChange: (theme: 'light' | 'dark' | 'system') => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ currentTheme, onThemeChange }) => {
  const [settings, setSettings] = useState<AppSettings>({
    camera_resolution: '1280x720',
    target_camera_fps: 60,
    target_sender_fps: 30,
    qr_error_correction: 'M',
    download_path: 'received_files',
    theme: currentTheme,
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSettings().then(setSettings).catch(() => {});
  }, []);

  const handleChange = (key: keyof AppSettings, val: any) => {
    const updated = { ...settings, [key]: val };
    setSettings(updated);
    if (key === 'theme') {
      onThemeChange(val);
    }
  };

  const handleSave = async () => {
    await updateSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="settings-page animate-fade-in">
      <div className="card card-large settings-grid">
        {/* Camera Section */}
        <div className="settings-section">
          <div className="section-title">
            <Camera size={20} color="var(--accent-primary)" />
            <h3>Camera Acquisition</h3>
          </div>

          <div className="setting-row">
            <div className="setting-label">
              <span>Resolution</span>
              <p>Requested camera frame width & height</p>
            </div>
            <select
              className="setting-input"
              value={settings.camera_resolution}
              onChange={(e) => handleChange('camera_resolution', e.target.value)}
            >
              <option value="1280x720">1280 × 720 (HD)</option>
              <option value="1920x1080">1920 × 1080 (Full HD)</option>
              <option value="640x480">640 × 480 (SD)</option>
            </select>
          </div>

          <div className="setting-row">
            <div className="setting-label">
              <span>Target Camera FPS</span>
              <p>Hardware acquisition frame rate</p>
            </div>
            <select
              className="setting-input"
              value={settings.target_camera_fps}
              onChange={(e) => handleChange('target_camera_fps', Number(e.target.value))}
            >
              <option value={30}>30 FPS</option>
              <option value={60}>60 FPS</option>
              <option value={120}>120 FPS</option>
            </select>
          </div>
        </div>

        {/* Sender Section */}
        <div className="settings-section">
          <div className="section-title">
            <Sliders size={20} color="var(--accent-primary)" />
            <h3>Transmission Engine</h3>
          </div>

          <div className="setting-row">
            <div className="setting-label">
              <span>Display FPS Target</span>
              <p>Sender screen render refresh rate</p>
            </div>
            <select
              className="setting-input"
              value={settings.target_sender_fps}
              onChange={(e) => handleChange('target_sender_fps', Number(e.target.value))}
            >
              <option value={15}>15 FPS</option>
              <option value={30}>30 FPS</option>
              <option value={60}>60 FPS</option>
            </select>
          </div>

          <div className="setting-row">
            <div className="setting-label">
              <span>QR Error Correction</span>
              <p>Reed-Solomon redundancy level</p>
            </div>
            <select
              className="setting-input"
              value={settings.qr_error_correction}
              onChange={(e) => handleChange('qr_error_correction', e.target.value)}
            >
              <option value="L">Low (7% recovery)</option>
              <option value="M">Medium (15% recovery)</option>
              <option value="Q">Quartile (25% recovery)</option>
              <option value="H">High (30% recovery)</option>
            </select>
          </div>
        </div>

        {/* Storage Section */}
        <div className="settings-section">
          <div className="section-title">
            <Folder size={20} color="var(--accent-primary)" />
            <h3>Storage & Output</h3>
          </div>

          <div className="setting-row">
            <div className="setting-label">
              <span>Received Files Directory</span>
              <p>Output path for reconstructed files</p>
            </div>
            <input
              type="text"
              className="setting-input-text font-mono"
              value={settings.download_path}
              onChange={(e) => handleChange('download_path', e.target.value)}
            />
          </div>
        </div>

        {/* Theme Section */}
        <div className="settings-section">
          <div className="section-title">
            <Sun size={20} color="var(--accent-primary)" />
            <h3>Appearance Theme</h3>
          </div>

          <div className="theme-options-row">
            <button
              className={`theme-card-btn ${settings.theme === 'light' ? 'selected' : ''}`}
              onClick={() => handleChange('theme', 'light')}
            >
              <Sun size={20} />
              <span>Light</span>
            </button>

            <button
              className={`theme-card-btn ${settings.theme === 'dark' ? 'selected' : ''}`}
              onClick={() => handleChange('theme', 'dark')}
            >
              <Moon size={20} />
              <span>Dark</span>
            </button>
          </div>
        </div>

        <div className="settings-footer">
          <button className="btn-primary" onClick={handleSave}>
            {saved ? <Check size={18} /> : null}
            <span>{saved ? 'Settings Saved ✓' : 'Save Preferences'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
