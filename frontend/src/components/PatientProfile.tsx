import { useState, useEffect } from 'react';
import { User, Phone, Mail, MapPin, Activity, RefreshCw, ArrowLeft, Clock } from 'lucide-react';
import { PatientDetail, Report } from '../types';
import { ReportCard } from './ReportCard';
import { LoadingSpinner } from './common/LoadingSpinner';
import { api } from '../api/client';

interface PatientProfileProps {
  patientId: string;
  onBack?: () => void;
}

export function PatientProfile({ patientId, onBack }: PatientProfileProps) {
  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyTab, setHistoryTab] = useState<'report' | 'readings'>('report');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const pData = await api.getPatient(patientId);
      setPatient(pData);

      try {
        const rData = await api.getLatestReport(patientId);
        setReport(rData);
      } catch {
        // Report might not exist yet
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch patient data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [patientId]);

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    try {
      const newReport = await api.generateReport(patientId);
      setReport(newReport);
    } catch (err: any) {
      setError(err.message || 'Failed to generate new report.');
    } finally {
      setGeneratingReport(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Retrieving clinical records..." />;
  }

  if (error || !patient) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--status-diabetes)', marginBottom: '1rem' }}>{error || 'Patient not found'}</p>
        <button onClick={loadData} style={{ padding: '0.5rem 1rem', backgroundColor: 'var(--accent-primary)', color: '#fff', borderRadius: 'var(--radius-md)' }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Back button */}
      {onBack && (
        <button
          onClick={onBack}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.85rem' }}
        >
          <ArrowLeft size={16} /> Back to Patient Directory
        </button>
      )}

      {/* Patient Demographic Profile Card */}
      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                backgroundColor: 'rgba(14, 165, 233, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid rgba(14, 165, 233, 0.3)',
              }}
            >
              <User size={26} color="var(--accent-primary)" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>{patient.name}</h2>
                <span
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  {patient.patient_id}
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Registered Patient Telemetry Record</p>
            </div>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(14, 165, 233, 0.15)',
              border: '1px solid rgba(14, 165, 233, 0.35)',
              color: 'var(--accent-primary)',
              padding: '0.55rem 1rem',
              borderRadius: 'var(--radius-md)',
              fontWeight: 600,
              fontSize: '0.85rem',
              opacity: generatingReport ? 0.7 : 1,
            }}
          >
            <RefreshCw size={15} className={generatingReport ? 'spin' : ''} />
            {generatingReport ? 'Analyzing Readings...' : 'Regenerate 4-Week Report'}
          </button>
        </div>

        {/* Contact details row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginTop: '1.25rem',
            paddingTop: '1.25rem',
            borderTop: '1px solid var(--border-color)',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
            <Mail size={16} color="var(--accent-primary)" />
            <span>{patient.email}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
            <Phone size={16} color="var(--accent-primary)" />
            <span>{patient.phone}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
            <MapPin size={16} color="var(--accent-primary)" />
            <span>{patient.address}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
            <Activity size={16} color="var(--accent-primary)" />
            <span>{patient.readings ? patient.readings.length : 0} Telemetry Readings Recorded</span>
          </div>
        </div>
      </div>

      {/* Navigation tabs between 4-week Report and Raw Telemetry Readings */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <button
          onClick={() => setHistoryTab('report')}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            fontWeight: 600,
            backgroundColor: historyTab === 'report' ? 'var(--accent-primary)' : 'rgba(255, 255, 255, 0.05)',
            color: historyTab === 'report' ? '#fff' : 'var(--text-secondary)',
          }}
        >
          4-Week Clinical Report
        </button>
        <button
          onClick={() => setHistoryTab('readings')}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            fontWeight: 600,
            backgroundColor: historyTab === 'readings' ? 'var(--accent-primary)' : 'rgba(255, 255, 255, 0.05)',
            color: historyTab === 'readings' ? '#fff' : 'var(--text-secondary)',
          }}
        >
          Raw Glucose History ({patient.readings ? patient.readings.length : 0})
        </button>
      </div>

      {historyTab === 'report' && (
        <>
          {report ? (
            <ReportCard report={report} onEmailSent={loadData} />
          ) : (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                No 4-week report generated for this patient yet.
              </p>
              <button
                onClick={handleGenerateReport}
                disabled={generatingReport}
                style={{
                  padding: '0.6rem 1.25rem',
                  backgroundColor: 'var(--accent-primary)',
                  color: '#fff',
                  borderRadius: 'var(--radius-md)',
                  fontWeight: 600,
                }}
              >
                Generate 4-Week Report Now
              </button>
            </div>
          )}
        </>
      )}

      {historyTab === 'readings' && (
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Recorded Glucose Telemetry</h3>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px' }}>Week</th>
                  <th style={{ padding: '8px' }}>Timestamp</th>
                  <th style={{ padding: '8px' }}>Context</th>
                  <th style={{ padding: '8px' }}>Glucose (mg/dL)</th>
                </tr>
              </thead>
              <tbody>
                {(patient.readings || []).map((r) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>Week {r.week_number}</td>
                    <td style={{ padding: '8px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> {new Date(r.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '8px', textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                      {r.meal_context || 'Random'}
                    </td>
                    <td style={{ padding: '8px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: r.glucose_value >= 126 ? '#ef4444' : r.glucose_value < 70 ? '#a855f7' : '#10b981' }}>
                      {r.glucose_value.toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
