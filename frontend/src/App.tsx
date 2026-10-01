import { useState } from 'react';
import { Activity, Users, MessageSquare, ShieldCheck } from 'lucide-react';
import { Dashboard } from './components/Dashboard';
import { PatientList } from './components/PatientList';
import { PatientProfile } from './components/PatientProfile';
import { AIChat } from './components/AIChat';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'patients' | 'profile' | 'chat'>('dashboard');
  const [selectedPatientId, setSelectedPatientId] = useState<string>('P015');
  const [chatInitialPrompt, setChatInitialPrompt] = useState<string>('');

  const handleSelectPatient = (patientId: string) => {
    setSelectedPatientId(patientId);
    setActiveTab('profile');
  };

  const handleNavigateToChat = (prompt?: string) => {
    if (prompt) setChatInitialPrompt(prompt);
    setActiveTab('chat');
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', flexDirection: 'column' }}>
      {/* Top Header */}
      <header
        style={{
          borderBottom: '1px solid var(--border-color)',
          backgroundColor: 'rgba(11, 15, 25, 0.85)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
          padding: '0 2rem',
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => setActiveTab('dashboard')}>
          <div
            style={{
              background: 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
              padding: '8px',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 15px rgba(14, 165, 233, 0.4)',
            }}
          >
            <Activity size={22} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.15rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#f8fafc' }}>
              Spundan <span style={{ color: 'var(--accent-primary)', fontWeight: 400 }}>GlucoseCare</span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Hospital Patient Monitoring & AI Reporting</p>
          </div>
        </div>

        <nav style={{ display: 'flex', gap: '0.5rem' }}>
          {[
            { id: 'dashboard', label: 'Dashboard', icon: Activity },
            { id: 'patients', label: 'Patients', icon: Users },
            { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id || (tab.id === 'patients' && activeTab === 'profile');
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
                  backgroundColor: isActive ? 'rgba(14, 165, 233, 0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(14, 165, 233, 0.3)' : '1px solid transparent',
                  cursor: 'pointer',
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
          <span>Clinical System Online</span>
        </div>
      </header>

      {/* Main Container */}
      <main style={{ flex: 1, padding: '2rem', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        {activeTab === 'dashboard' && (
          <Dashboard onSelectPatient={handleSelectPatient} onNavigateToChat={handleNavigateToChat} />
        )}

        {activeTab === 'patients' && (
          <PatientList onSelectPatient={handleSelectPatient} />
        )}

        {activeTab === 'profile' && (
          <PatientProfile
            patientId={selectedPatientId}
            onBack={() => setActiveTab('patients')}
          />
        )}

        {activeTab === 'chat' && (
          <AIChat initialPrompt={chatInitialPrompt} />
        )}
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-color)',
          padding: '1.25rem 2rem',
          textAlign: 'center',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          backgroundColor: 'rgba(11, 15, 25, 0.5)',
        }}
      >
        Hospital Patient Glucose Monitoring & AI Reporting System &bull; Production Platform &copy; 2026
      </footer>
    </div>
  );
}
