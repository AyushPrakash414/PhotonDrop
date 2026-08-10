import React from 'react';
import { Sun, Moon, ShieldCheck } from 'lucide-react';
import './Header.css';

interface HeaderProps {
  title: string;
  subtitle?: string;
  theme: 'light' | 'dark' | 'system';
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, theme, onToggleTheme }) => {
  return (
    <header className="app-header">
      <div className="header-left">
        <div className="mobile-brand">
          <div className="brand-logo">
            <div className="logo-dot" />
          </div>
          <span className="mobile-brand-title">PhotonDrop</span>
        </div>
        <div className="header-titles">
          <h1>{title}</h1>
          {subtitle && <p className="header-subtitle">{subtitle}</p>}
        </div>
      </div>

      <div className="header-actions">
        <div className="security-badge">
          <ShieldCheck size={16} color="var(--success)" />
          <span className="badge-text">Zero Network</span>
        </div>

        <button className="theme-toggle-btn" onClick={onToggleTheme} title="Toggle Theme">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
};
