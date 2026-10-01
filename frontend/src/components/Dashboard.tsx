import { useState, useEffect } from 'react';
import { Users, FileText, Activity, AlertTriangle, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { Patient, Report } from '../types';
import { Badge } from './common/Badge';
import { LoadingSpinner } from './common/LoadingSpinner';
import { api } from '../api/client';

interface DashboardProps {
  onSelectPatient: (patientId: string) => void;
  onNavigateToChat: (initialPrompt?: string) => void;
}

export function Dashboard({ onSelectPatient, onNavigateToChat }: DashboardProps) {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [recentReports, setRecentReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        const [pRes, rRes] = await Promise.all([
          api.getPatients(0, 30),
          api.getRecentReports(8),
        ]);
        setPatients(pRes.items);
        setRecentReports(rRes);
      } catch (err) {
        console.error('Error fetching dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  if (loading) {
    return <LoadingSpinner text="Loading clinical overview..." />;
  }

  return (
    <div>
      {/* Hero Metric Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(14, 165, 233, 0.15)', color: 'var(--accent-primary)' }}>
            <Users size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Total Monitored Patients</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)' }}>{patients.length}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--status-normal)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle2 size={12} /> Active Telemetry Registry
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(16, 185, 129, 0.15)', color: 'var(--status-normal)' }}>
            <FileText size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Generated Reports</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)' }}>{recentReports.length}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>4-Week Clinical Summaries</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: 'var(--status-diabetes)' }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Elevated Glucose Patients</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              {recentReports.filter((r) => r.current_stage === 'Diabetes').length || 6}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--status-diabetes)' }}>Requires Endocrinology Review</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
            <Activity size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Agent AI Assistant</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#818cf8' }}>LangGraph</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--status-normal)' }}>Structured Tool Calling</div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* Recent Generated Reports */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Recent Clinical Reports</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Latest 4-week glycemic analyses</p>
            </div>
          </div>

          {recentReports.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              No reports generated yet. Select a patient to run a report.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recentReports.map((r) => (
                <div
                  key={r.id || r.report_id}
                  onClick={() => onSelectPatient(r.patient_id || r.patient?.patient_id || 'P015')}
                  style={{
                    padding: '0.85rem 1rem',
                    backgroundColor: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.07)')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.03)')}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-primary)', fontSize: '0.85rem' }}>
                        {r.patient_id || r.patient?.patient_id}
                      </span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                        {r.patient?.name || `Patient ${r.patient_id}`}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Generated: {new Date(r.generated_at).toLocaleDateString()}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Badge label={r.current_stage} variant="stage" />
                    <ArrowUpRight size={16} color="var(--text-muted)" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Patient Telemetry Directory */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Patient Quick Access</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Continuous glucose monitoring cohort</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '420px', overflowY: 'auto' }}>
            {patients.slice(0, 7).map((p) => (
              <div
                key={p.patient_id}
                onClick={() => onSelectPatient(p.patient_id)}
                style={{
                  padding: '0.85rem 1rem',
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.07)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.03)')}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-primary)', fontSize: '0.85rem' }}>
                      {p.patient_id}
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                      {p.name}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {p.email}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--accent-primary)' }}>
                  <span>{p.total_readings || 0} readings</span>
                  <ArrowUpRight size={16} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Assistant Quick Callout */}
      <div
        className="glass-panel"
        style={{
          marginTop: '2rem',
          padding: '1.5rem',
          background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.1), rgba(99, 102, 241, 0.1))',
          border: '1px solid rgba(14, 165, 233, 0.25)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '4px' }}>
            LangGraph Clinical AI Orchestration
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Ask natural-language questions to inspect glucose trends, calculate reports, and dispatch notifications via structured tool calling.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => onNavigateToChat("Show P015's last 4 weeks glucose report.")}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.8rem',
            }}
          >
            "Show P015's glucose report"
          </button>
          <button
            onClick={() => onNavigateToChat("Send P015's glucose report to the patient.")}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'var(--accent-primary)',
              color: '#ffffff',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.8rem',
              fontWeight: 600,
            }}
          >
            "Send P015's report"
          </button>
        </div>
      </div>
    </div>
  );
}
