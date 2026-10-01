interface BadgeProps {
  label: string;
  variant?: 'stage' | 'trend' | 'status';
}

export function Badge({ label, variant = 'stage' }: BadgeProps) {
  const norm = label?.toLowerCase() || '';

  let bg = 'rgba(148, 163, 184, 0.12)';
  let color = '#94a3b8';
  let border = 'rgba(148, 163, 184, 0.25)';

  if (norm.includes('normal')) {
    bg = 'rgba(16, 185, 129, 0.12)';
    color = '#10b981';
    border = 'rgba(16, 185, 129, 0.3)';
  } else if (norm.includes('prediabetes') || norm.includes('pre-diabetes')) {
    bg = 'rgba(245, 158, 11, 0.12)';
    color = '#f59e0b';
    border = 'rgba(245, 158, 11, 0.3)';
  } else if (norm.includes('diabetes')) {
    bg = 'rgba(239, 68, 68, 0.12)';
    color = '#ef4444';
    border = 'rgba(239, 68, 68, 0.3)';
  } else if (norm.includes('hypo')) {
    bg = 'rgba(139, 92, 246, 0.12)';
    color = '#a855f7';
    border = 'rgba(139, 92, 246, 0.3)';
  } else if (norm.includes('improving')) {
    bg = 'rgba(16, 185, 129, 0.12)';
    color = '#34d399';
    border = 'rgba(16, 185, 129, 0.3)';
  } else if (norm.includes('worsening')) {
    bg = 'rgba(239, 68, 68, 0.12)';
    color = '#f87171';
    border = 'rgba(239, 68, 68, 0.3)';
  } else if (norm.includes('stable')) {
    bg = 'rgba(14, 165, 233, 0.12)';
    color = '#38bdf8';
    border = 'rgba(14, 165, 233, 0.3)';
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '3px 9px',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: 600,
        backgroundColor: bg,
        color: color,
        border: `1px solid ${border}`,
        letterSpacing: '0.02em',
        textTransform: variant === 'trend' ? 'capitalize' : 'none',
      }}
    >
      {label}
    </span>
  );
}
