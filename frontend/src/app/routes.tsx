import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Dashboard } from '../pages/Dashboard';
import { SendPage } from '../pages/SendPage';
import { ReceivePage } from '../pages/ReceivePage';
import { ActivityPage } from '../pages/ActivityPage';
import { SettingsPage } from '../pages/SettingsPage';

interface AppRoutesProps {
  theme: 'light' | 'dark' | 'system';
  onThemeChange: (theme: 'light' | 'dark' | 'system') => void;
}

export const AppRoutes: React.FC<AppRoutesProps> = ({ theme, onThemeChange }) => {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/send" element={<SendPage />} />
      <Route path="/receive" element={<ReceivePage />} />
      <Route path="/activity" element={<ActivityPage />} />
      <Route path="/settings" element={<SettingsPage currentTheme={theme} onThemeChange={onThemeChange} />} />
    </Routes>
  );
};
