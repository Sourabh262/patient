import { Patient, PatientDetail, Report } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || response.statusText;
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Patients
  async getPatients(skip = 0, limit = 50, search?: string): Promise<{ items: Patient[]; meta: any }> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (search?.trim()) {
      params.append('search', search.trim());
    }
    return request<{ items: Patient[]; meta: any }>(`/patients?${params.toString()}`);
  },

  async getPatient(patientId: string): Promise<PatientDetail> {
    return request<PatientDetail>(`/patients/${encodeURIComponent(patientId)}`);
  },

  async getPatientReadings(patientId: string) {
    return request<{ patient_id: string; total_readings: number; readings: any[] }>(
      `/patients/${encodeURIComponent(patientId)}/readings`
    );
  },

  // Reports
  async generateReport(patientId: string): Promise<Report> {
    return request<Report>('/reports/generate', {
      method: 'POST',
      body: JSON.stringify({ patient_id: patientId }),
    });
  },

  async getLatestReport(patientId: string): Promise<Report> {
    return request<Report>(`/reports/latest/${encodeURIComponent(patientId)}`);
  },

  async getRecentReports(limit = 10): Promise<Report[]> {
    return request<Report[]>(`/reports?limit=${limit}`);
  },

  async sendReportEmail(reportId: number): Promise<{ status: string; message: string }> {
    return request<{ status: string; message: string }>(`/reports/${reportId}/send-email`, {
      method: 'POST',
    });
  },

  // AI Chat
  async sendChatMessage(message: string): Promise<{ response: string; messages: any[] }> {
    return request<{ response: string; messages: any[] }>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
};
