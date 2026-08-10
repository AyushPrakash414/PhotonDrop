import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { AppRoutes } from './routes';
import { useTransfer } from '../hooks/useTransfer';
import '../styles/globals.css';
import './App.css';

const _PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard', subtitle: 'Overview of screen-to-camera optical transport' },
  '/send': { title: 'Send File', subtitle: 'Transmit arbitrary binary files through visible light' },
  '/receive': { title: 'Receive File', subtitle: 'Point your camera at sender display to recover files' },
  '/activity': { title: 'Transfer Activity', subtitle: 'Local log of completed optical file transfers' },
  '/settings': { title: 'Settings', subtitle: 'Configure acquisition resolution, FPS, and storage' },
};

export const App: React.FC = () => {
  const location = useLocation();
  const { isOpticalLinkActive } = useTransfer();

  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>(() => {
    return (localStorage.getItem('photondrop_theme') as any) || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('photondrop_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const pageInfo = _PAGE_TITLES[location.pathname] || { title: 'PhotonDrop', subtitle: '' };

  return (
    <div className="app-layout">
      <Sidebar isOpticalLinkActive={isOpticalLinkActive} />

      <div className="app-main">
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          theme={theme}
          onToggleTheme={toggleTheme}
        />
        <main className="app-content">
          <AppRoutes theme={theme} onThemeChange={setTheme} />
        </main>
      </div>
    </div>
  );
};
