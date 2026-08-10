import React from 'react';
import { NavLink } from 'react-router-dom';
import { Send, Download, Activity, Settings, Radio } from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  isOpticalLinkActive: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpticalLinkActive }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">
          <div className="logo-dot" />
        </div>
        <div className="brand-text">
          <h2>PhotonDrop</h2>
          <span>Optical File Transfer</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Activity size={20} />
          <span>Dashboard</span>
        </NavLink>
        <NavLink to="/send" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Send size={20} />
          <span>Send File</span>
        </NavLink>
        <NavLink to="/receive" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Download size={20} />
          <span>Receive File</span>
        </NavLink>
        <NavLink to="/activity" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Activity size={20} />
          <span>Activity</span>
        </NavLink>
        <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Settings size={20} />
          <span>Settings</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className={`optical-link-card ${isOpticalLinkActive ? 'active' : ''}`}>
          <Radio size={18} className={isOpticalLinkActive ? 'animate-signal-glow' : ''} />
          <div className="link-status">
            <span className="link-title">Optical Link</span>
            <span className="link-state">
              {isOpticalLinkActive ? '● Transmitting / Active' : '● Ready'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
