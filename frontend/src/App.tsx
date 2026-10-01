import { useState } from 'react';
import { Activity, Users, FileText, MessageSquare, ShieldCheck } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'patients' | 'reports' | 'chat'>('dashboard');

  return (
    <div style={{ display: 'flex', minHeight: '100vh', flexDirection: 'column' }}>
      {/* Top Navigation */}
      <header style={{
        borderBottom: '1px solid var(--border-color)',
        backgroundColor: 'rgba(11, 15, 25, 0.8)',
        backdropFilter: 'blur(8px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '0 2rem',
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
            padding: '8px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(14, 165, 233, 0.4)'
          }}>
            <Activity size={22} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.15rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#f8fafc' }}>
              Spundan <span style={{ color: 'var(--accent-primary)', fontWeight: 400 }}>GlucoseCare</span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>AI-Powered Patient Monitoring & Reporting</p>
          </div>
        </div>

        <nav style={{ display: 'flex', gap: '0.5rem' }}>
          {[
            { id: 'dashboard', label: 'Dashboard', icon: Activity },
            { id: 'patients', label: 'Patients', icon: Users },
            { id: 'reports', label: 'Reports', icon: FileText },
            { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  backgroundColor: isActive ? 'rgba(14, 165, 233, 0.1)' : 'transparent',
                  border: isActive ? '1px solid rgba(14, 165, 233, 0.3)' : '1px solid transparent',
                  cursor: 'pointer'
                }}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--status-normal)' }}>
          <ShieldCheck size={16} />
          <span>System Online</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '2rem', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center' }}>
          <div style={{
            display: 'inline-flex',
            padding: '12px',
            borderRadius: '50%',
            backgroundColor: 'rgba(14, 165, 233, 0.1)',
            marginBottom: '1rem'
          }}>
            <Activity size={36} color="var(--accent-primary)" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.75rem' }}>
            Patient Glucose Monitoring & AI Clinical Reporting
          </h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '650px', margin: '0 auto 1.5rem', fontSize: '0.95rem' }}>
            Production-grade clinical platform providing automated 4-week glucose tracking,
            deterministic stage classification, LangGraph AI orchestration, and direct patient email reports.
          </p>
          <div style={{ display: 'inline-flex', gap: '1rem' }}>
            <span style={{
              padding: '0.35rem 0.85rem',
              borderRadius: '9999px',
              fontSize: '0.8rem',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)'
            }}>
              Active Tab: <strong style={{ color: '#fff', textTransform: 'capitalize' }}>{activeTab}</strong>
            </span>
            <span style={{
              padding: '0.35rem 0.85rem',
              borderRadius: '9999px',
              fontSize: '0.8rem',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              color: 'var(--status-normal)'
            }}>
              API Target: http://localhost:8000
            </span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-color)',
        padding: '1.25rem 2rem',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: 'var(--text-muted)'
      }}>
        Hospital Glucose Monitoring & AI Reporting System &copy; 2026. Production Health Platform.
      </footer>
    </div>
  );
}
