import { useState, useEffect } from 'react';
import { Search, ChevronRight, User, Activity } from 'lucide-react';
import { Patient } from '../types';
import { LoadingSpinner } from './common/LoadingSpinner';
import { api } from '../api/client';

interface PatientListProps {
  onSelectPatient: (patientId: string) => void;
}

export function PatientList({ onSelectPatient }: PatientListProps) {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPatients = async (query = '') => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getPatients(0, 50, query);
      setPatients(res.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load patient records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPatients(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  return (
    <div>
      {/* Header & Search Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-primary)' }}>Patient Directory</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Search and select from registered hospital glucose monitoring patients
          </p>
        </div>

        {/* Search input */}
        <div style={{ position: 'relative', width: '320px', maxWidth: '100%' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID (e.g. P015), name, or email..."
            style={{
              width: '100%',
              padding: '0.6rem 1rem 0.6rem 2.25rem',
              backgroundColor: 'rgba(17, 24, 39, 0.7)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              outline: 'none',
            }}
          />
        </div>
      </div>

      {loading && <LoadingSpinner text="Searching patients..." />}

      {error && (
        <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
          <p>{error}</p>
          <button onClick={() => fetchPatients(search)} style={{ marginTop: '0.75rem', padding: '0.5rem 1rem', backgroundColor: 'var(--accent-primary)', color: '#fff', borderRadius: 'var(--radius-md)' }}>
            Retry
          </button>
        </div>
      )}

      {!loading && !error && patients.length === 0 && (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <User size={36} color="var(--text-muted)" style={{ marginBottom: '0.5rem' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>No patients found</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>No patient records matched '{search}'</p>
        </div>
      )}

      {/* Patients Grid */}
      {!loading && !error && patients.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
          {patients.map((p) => (
            <div
              key={p.patient_id}
              onClick={() => onSelectPatient(p.patient_id)}
              className="glass-panel"
              style={{
                padding: '1.25rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'rgba(14, 165, 233, 0.5)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-color)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      color: 'var(--accent-primary)',
                      backgroundColor: 'rgba(14, 165, 233, 0.1)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    {p.patient_id}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <Activity size={12} color="var(--accent-primary)" />
                    <span>{p.total_readings || 0} readings</span>
                  </div>
                </div>

                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  {p.name}
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  {p.email}
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {p.address}
                </p>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: '4px',
                  marginTop: '1rem',
                  paddingTop: '0.75rem',
                  borderTop: '1px solid var(--border-color)',
                  color: 'var(--accent-primary)',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                }}
              >
                <span>View Full Telemetry & Report</span>
                <ChevronRight size={14} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
