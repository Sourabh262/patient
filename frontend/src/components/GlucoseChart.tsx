import { useState } from 'react';
import { WeeklyAverages, WeeklyStages } from '../types';

interface GlucoseChartProps {
  averages: WeeklyAverages;
  stages: WeeklyStages;
}

export function GlucoseChart({ averages, stages }: GlucoseChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);

  const weeks = [1, 2, 3, 4];
  const points = weeks.map((w) => {
    const val = averages[`week_${w}`];
    return {
      week: w,
      val: val !== undefined && val !== null ? val : null,
      stage: stages[`week_${w}`] || 'No Data',
    };
  });

  // SVG dimensions
  const width = 600;
  const height = 260;
  const padding = { top: 25, right: 35, bottom: 45, left: 55 };

  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Glucose scale: min 50 to max 220
  const minY = 50;
  const maxY = 220;

  const getX = (w: number) => padding.left + ((w - 1) / (weeks.length - 1)) * chartW;
  const getY = (val: number) => {
    const clamped = Math.max(minY, Math.min(maxY, val));
    return padding.top + chartH - ((clamped - minY) / (maxY - minY)) * chartH;
  };

  // Threshold Y positions
  const yHypo = getY(70);
  const yNormal = getY(99);
  const yPrediabetes = getY(125);

  // Line path
  const validPoints = points.filter((p): p is { week: number; val: number; stage: string } => p.val !== null);
  const pathD = validPoints.reduce((acc, p, idx) => {
    const x = getX(p.week);
    const y = getY(p.val);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            4-Week Glucose Progression
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Weekly average glucose telemetry vs. clinical reference ranges
          </p>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10b981' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981' }} /> Normal (&le;99)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#f59e0b' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#f59e0b' }} /> Pre-diabetes (100-125)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#ef4444' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#ef4444' }} /> Diabetes (&ge;126)
          </span>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          <defs>
            <linearGradient id="glucoseLineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="100%" stopColor="#0ea5e9" />
            </linearGradient>
            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Reference range zones */}
          {/* Diabetes Zone (above 125) */}
          <rect
            x={padding.left}
            y={padding.top}
            width={chartW}
            height={Math.max(0, yPrediabetes - padding.top)}
            fill="rgba(239, 68, 68, 0.05)"
          />
          {/* Pre-diabetes Zone (99 to 125) */}
          <rect
            x={padding.left}
            y={yPrediabetes}
            width={chartW}
            height={Math.max(0, yNormal - yPrediabetes)}
            fill="rgba(245, 158, 11, 0.05)"
          />
          {/* Normal Zone (70 to 99) */}
          <rect
            x={padding.left}
            y={yNormal}
            width={chartW}
            height={Math.max(0, yHypo - yNormal)}
            fill="rgba(16, 185, 129, 0.06)"
          />
          {/* Hypo Zone (< 70) */}
          <rect
            x={padding.left}
            y={yHypo}
            width={chartW}
            height={Math.max(0, padding.top + chartH - yHypo)}
            fill="rgba(139, 92, 246, 0.05)"
          />

          {/* Threshold dashed lines */}
          <line x1={padding.left} y1={yPrediabetes} x2={padding.left + chartW} y2={yPrediabetes} stroke="rgba(245, 158, 11, 0.3)" strokeDasharray="3 3" />
          <line x1={padding.left} y1={yNormal} x2={padding.left + chartW} y2={yNormal} stroke="rgba(16, 185, 129, 0.3)" strokeDasharray="3 3" />
          <line x1={padding.left} y1={yHypo} x2={padding.left + chartW} y2={yHypo} stroke="rgba(139, 92, 246, 0.3)" strokeDasharray="3 3" />

          {/* Y Axis Labels */}
          {[60, 99, 125, 160, 200].map((val) => {
            const y = getY(val);
            return (
              <text key={val} x={padding.left - 10} y={y + 4} textAnchor="end" fill="#64748b" fontSize="10" fontFamily="JetBrains Mono, monospace">
                {val}
              </text>
            );
          })}

          {/* X Axis Labels */}
          {weeks.map((w) => {
            const x = getX(w);
            return (
              <text key={w} x={x} y={padding.top + chartH + 24} textAnchor="middle" fill="#94a3b8" fontSize="12" fontWeight="500">
                Week {w}
              </text>
            );
          })}

          {/* Polyline Path */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="url(#glucoseLineGradient)"
              strokeWidth="3.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ filter: 'drop-shadow(0 2px 8px rgba(14, 165, 233, 0.5))' }}
            />
          )}

          {/* Data Points */}
          {validPoints.map((p) => {
            const cx = getX(p.week);
            const cy = getY(p.val);
            const isHovered = hoveredPoint === p.week;

            let pointColor = '#10b981';
            if (p.stage === 'Pre-diabetes') pointColor = '#f59e0b';
            else if (p.stage === 'Diabetes') pointColor = '#ef4444';
            else if (p.stage === 'Hypoglycemia') pointColor = '#8b5cf6';

            return (
              <g key={p.week} onMouseEnter={() => setHoveredPoint(p.week)} onMouseLeave={() => setHoveredPoint(null)} style={{ cursor: 'pointer' }}>
                <circle cx={cx} cy={cy} r={isHovered ? 8 : 5} fill={pointColor} stroke="#ffffff" strokeWidth="2.5" />
                {/* Floating label */}
                <text
                  x={cx}
                  y={cy - 12}
                  textAnchor="middle"
                  fill="#f8fafc"
                  fontSize="11"
                  fontWeight="700"
                  fontFamily="JetBrains Mono, monospace"
                >
                  {p.val.toFixed(1)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
