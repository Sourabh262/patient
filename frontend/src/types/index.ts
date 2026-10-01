export interface Patient {
  patient_id: str;
  name: string;
  phone: string;
  email: string;
  address: string;
  created_at: string;
  updated_at: string;
  total_readings?: number;
}

type str = string;

export interface GlucoseReading {
  id: number;
  patient_id: string;
  glucose_value: number;
  week_number: number;
  meal_context?: string;
  timestamp: string;
}

export interface PatientDetail extends Patient {
  readings: GlucoseReading[];
}

export interface WeeklyAverages {
  week_1: number | null;
  week_2: number | null;
  week_3: number | null;
  week_4: number | null;
  [key: string]: number | null;
}

export interface WeeklyStages {
  week_1: string;
  week_2: string;
  week_3: string;
  week_4: string;
  [key: string]: string;
}

export interface Report {
  id?: number;
  report_id?: number;
  patient_id?: string;
  generated_at: string;
  patient?: Patient;
  weekly_averages: WeeklyAverages;
  weekly_stages: WeeklyStages;
  current_stage: string;
  trend: 'improving' | 'worsening' | 'stable' | 'fluctuating' | 'insufficient_data' | string;
  ai_summary: string;
  email_sent: boolean;
  email_sent_at?: string | null;
  email_recipient?: string | null;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  toolCalls?: Array<{
    name: string;
    args: Record<string, any>;
  }>;
}

export interface DashboardMetrics {
  totalPatients: number;
  normalCount: number;
  prediabetesCount: number;
  diabetesCount: number;
  hypoCount: number;
  recentReports: Report[];
}
