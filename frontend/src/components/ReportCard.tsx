import { useState } from 'react';
import { Mail, Calendar, TrendingUp, TrendingDown, Minus, Sparkles, CheckCircle2 } from 'lucide-react';
import { Report } from '../types';
import { Badge } from './common/Badge';
import { GlucoseChart } from './GlucoseChart';
import { api } from '../api/client';

interface ReportCardProps {
  report: Report;
  onEmailSent?: () => void;
  showChart?: boolean;
}

export function ReportCard({ report, onEmailSent, showChart = true }: ReportCardProps) {
  const [isSending, setIsSending] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSendEmail = async () => {
    const rId = report.report_id || report.id;
    if (!rId) {
      setStatusMsg({ type: 'error', text: 'Report ID is not available' });
      setIsSending(false);
      return;
    }
    try {
      const res = await api.sendReportEmail(rId);
      setStatusMsg({ type: 'success', text: res.message || 'Report sent to patient email!' });
      if (onEmailSent) onEmailSent();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to dispatch email' });
    } finally {
      setIsSending(false);
    }
  };

  const trendIcon = () => {
    if (report.trend === 'improving') return <TrendingDown size={18} color="#10b981" />;
    if (report.trend === 'worsening') return <TrendingUp size={18} color="#ef4444" />;
    return <Minus size={18} color="#38bdf8" />;
  };

  return (
    <div className="glass-panel" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              4-Week Clinical Glucose Report
            </h2>
            <Badge label={report.current_stage} variant="stage" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Calendar size={14} /> Generated: {new Date(report.generated_at).toLocaleDateString()}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {trendIcon()} Trend: <strong style={{ color: '#fff', textTransform: 'capitalize' }}>{report.trend}</strong>
            </span>
          </div>
        </div>

        {/* Email button action */}
        <div>
          <button
            onClick={handleSendEmail}
            disabled={isSending}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: 'var(--accent-primary)',
              color: '#ffffff',
              padding: '0.55rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              fontWeight: 600,
              fontSize: '0.875rem',
              opacity: isSending ? 0.7 : 1,
              boxShadow: '0 2px 10px rgba(14, 165, 233, 0.3)',
            }}
          >
            <Mail size={16} />
            {isSending ? 'Sending to Patient...' : report.email_sent ? 'Resend Report Email' : 'Send Report to Patient'}
          </button>
          {report.email_sent && (
            <p style={{ fontSize: '0.75rem', color: 'var(--status-normal)', marginTop: '4px', textAlign: 'right', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
              <CheckCircle2 size={12} /> Emailed to {report.email_recipient || 'patient'}
            </p>
          )}
        </div>
      </div>

      {statusMsg && (
        <div
          style={{
            padding: '10px 14px',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1rem',
            fontSize: '0.85rem',
            backgroundColor: statusMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${statusMsg.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            color: statusMsg.type === 'success' ? '#34d399' : '#f87171',
          }}
        >
          {statusMsg.text}
        </div>
      )}

      {/* Optional Chart */}
      {showChart && <GlucoseChart averages={report.weekly_averages} stages={report.weekly_stages} />}

      {/* 4-Week Breakdown Cards */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
          Weekly Averages & Stage Breakdown
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '1rem' }}>
          {[1, 2, 3, 4].map((w) => {
            const avg = report.weekly_averages[`week_${w}`];
            const stage = report.weekly_stages[`week_${w}`] || 'No Data';
            return (
              <div
                key={w}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1rem',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Week {w}</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', marginBottom: '8px' }}>
                  {avg !== null && avg !== undefined ? `${avg.toFixed(1)}` : 'N/A'}
                  <span style={{ fontSize: '0.7rem', fontWeight: 400, color: 'var(--text-muted)', marginLeft: '2px' }}>mg/dL</span>
                </div>
                <Badge label={stage} variant="stage" />
              </div>
            );
          })}
        </div>
      </div>

      {/* Verified AI Summary */}
      <div style={{ backgroundColor: 'rgba(14, 165, 233, 0.04)', border: '1px solid rgba(14, 165, 233, 0.18)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <Sparkles size={16} color="var(--accent-primary)" />
          <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-primary)' }}>
            Clinical AI Summary
          </h4>
        </div>
        <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {report.ai_summary}
        </p>
      </div>
    </div>
  );
}
