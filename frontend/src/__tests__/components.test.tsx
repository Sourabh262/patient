import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Toast } from '../components/common/Toast';
import { GlucoseChart } from '../components/GlucoseChart';
import { ReportCard } from '../components/ReportCard';
import { Report } from '../types';

describe('Frontend Component Suite', () => {
  it('renders Badge with correct status label and styling', () => {
    render(<Badge label="Normal" variant="stage" />);
    expect(screen.getByText('Normal')).toBeInTheDocument();

    render(<Badge label="Diabetes" variant="stage" />);
    expect(screen.getByText('Diabetes')).toBeInTheDocument();

    render(<Badge label="improving" variant="trend" />);
    expect(screen.getByText('improving')).toBeInTheDocument();
  });

  it('renders LoadingSpinner with custom text', () => {
    render(<LoadingSpinner text="Loading clinical data..." />);
    expect(screen.getByText('Loading clinical data...')).toBeInTheDocument();
  });

  it('renders Toast and responds to close button click', () => {
    const handleClose = vi.fn();
    render(<Toast type="success" message="Report dispatched successfully" onClose={handleClose} />);
    expect(screen.getByText('Report dispatched successfully')).toBeInTheDocument();

    const closeBtn = screen.getByRole('button');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders GlucoseChart with weekly points and axis labels', () => {
    const averages = {
      week_1: 95.0,
      week_2: 110.0,
      week_3: 135.0,
      week_4: 145.0,
    };
    const stages = {
      week_1: 'Normal',
      week_2: 'Pre-diabetes',
      week_3: 'Diabetes',
      week_4: 'Diabetes',
    };

    render(<GlucoseChart averages={averages} stages={stages} />);
    expect(screen.getByText('4-Week Glucose Progression')).toBeInTheDocument();
    expect(screen.getByText('Week 1')).toBeInTheDocument();
    expect(screen.getByText('Week 4')).toBeInTheDocument();
  });

  it('renders ReportCard with 4-week metrics, stage badge, and AI summary', () => {
    const mockReport: Report = {
      report_id: 101,
      patient_id: 'P015',
      generated_at: new Date().toISOString(),
      weekly_averages: {
        week_1: 170.0,
        week_2: 165.0,
        week_3: 155.0,
        week_4: 150.0,
      },
      weekly_stages: {
        week_1: 'Diabetes',
        week_2: 'Diabetes',
        week_3: 'Diabetes',
        week_4: 'Diabetes',
      },
      current_stage: 'Diabetes',
      trend: 'improving',
      ai_summary: 'Patient demonstrates gradual improvement in blood glucose over 4 weeks.',
      email_sent: false,
    };

    render(<ReportCard report={mockReport} />);
    expect(screen.getByText('4-Week Clinical Glucose Report')).toBeInTheDocument();
    expect(screen.getAllByText('Diabetes').length).toBeGreaterThan(0);
    expect(screen.getByText(/Patient demonstrates gradual improvement/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Send Report to Patient/i })).toBeInTheDocument();
  });
});
