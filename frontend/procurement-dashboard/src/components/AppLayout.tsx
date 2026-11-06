import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  ShoppingCart, 
  Users, 
  FileText, 
  ShieldAlert, 
  History, 
  LogOut,
  Building2,
  UserCheck
} from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard Overview', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Purchase Requests', path: '/requests', icon: ShoppingCart },
    { name: 'Suppliers Directory', path: '/suppliers', icon: Users },
    { name: 'Quotations & OCR', path: '/quotations', icon: FileText },
    { name: 'Risk & Optimization', path: '/risk-optimization', icon: ShieldAlert },
    { name: 'Audit & Compliance', path: '/audit-trail', icon: History },
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif', backgroundColor: '#f8fafc' }}>
      {/* Sidebar */}
      <aside style={{ width: '260px', backgroundColor: '#0f172a', color: '#f1f5f9', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px 20px', borderBottom: '1px solid #1e293b' }}>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#38bdf8' }}>
            Procurement AI
          </h2>
          <span style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Intelligence Platform
          </span>
        </div>

        <nav style={{ flex: 1, padding: '16px 12px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  textDecoration: 'none',
                  fontSize: '14px',
                  marginBottom: '4px',
                  color: isActive ? '#ffffff' : '#94a3b8',
                  backgroundColor: isActive ? '#1e293b' : 'transparent',
                  fontWeight: isActive ? 600 : 400,
                  transition: 'background-color 0.2s',
                })}
              >
                <Icon size={18} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Card in Sidebar */}
        <div style={{ padding: '16px', borderTop: '1px solid #1e293b', backgroundColor: '#020617' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Building2 size={16} color="#38bdf8" />
            <span style={{ fontSize: '12px', fontWeight: 500, color: '#e2e8f0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.organization_name || 'Manufacturing Corp'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <UserCheck size={16} color="#4ade80" />
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '13px', fontWeight: 500, color: '#ffffff' }}>{user?.full_name}</div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>{user?.roles?.join(', ')}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '8px 12px',
              backgroundColor: '#ef4444',
              border: 'none',
              borderRadius: '4px',
              color: '#ffffff',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <header style={{ height: '64px', backgroundColor: '#ffffff', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 32px' }}>
          <h1 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#1e293b' }}>
            Sri Lankan Manufacturing Decision-Support
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '12px', backgroundColor: '#e0f2fe', color: '#0369a1', padding: '4px 10px', borderRadius: '12px', fontWeight: 500 }}>
              Stage 1 Foundation Ready
            </span>
          </div>
        </header>

        <main style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

