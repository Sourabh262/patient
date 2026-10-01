import { CheckCircle2, AlertCircle, X } from 'lucide-react';

interface ToastProps {
  type: 'success' | 'error' | 'info';
  message: string;
  onClose: () => void;
}

export function Toast({ type, message, onClose }: ToastProps) {
  const isSuccess = type === 'success';
  const isError = type === 'error';

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 100,
        backgroundColor: '#1e293b',
        border: `1px solid ${isSuccess ? '#10b981' : isError ? '#ef4444' : '#38bdf8'}`,
        color: '#f8fafc',
        padding: '12px 18px',
        borderRadius: '10px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        maxWidth: '420px',
        animation: 'slideUp 0.3s ease-out',
      }}
    >
      {isSuccess && <CheckCircle2 size={18} color="#10b981" />}
      {isError && <AlertCircle size={18} color="#ef4444" />}
      <span style={{ fontSize: '0.875rem', flex: 1 }}>{message}</span>
      <button onClick={onClose} style={{ color: '#94a3b8', display: 'flex', alignItems: 'center' }}>
        <X size={16} />
      </button>
      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
