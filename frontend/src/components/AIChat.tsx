import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Sparkles, Terminal, AlertCircle } from 'lucide-react';
import { ChatMessage } from '../types';
import { api } from '../api/client';

interface AIChatProps {
  initialPrompt?: string;
}

export function AIChat({ initialPrompt }: AIChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content:
        'Hello Doctor. I am your LangGraph Clinical AI Assistant for the Hospital Glucose Monitoring System. ' +
        'You can ask me to retrieve patient details, analyze 4-week glucose telemetry, generate reports, or dispatch patient emails using structured tool execution. ' +
        'Try asking: "Show P015\'s glucose report" or "Send P015\'s report".',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState(initialPrompt || '');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (initialPrompt) {
      setInput(initialPrompt);
    }
  }, [initialPrompt]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await api.sendChatMessage(query);

      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: 'assistant',
        content: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error communicating with AI assistant.');
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'system',
          content: `Unable to process request: ${err.message || 'Connection error'}. Please verify backend server is running.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const samplePrompts = [
    "Show P015's last 4 weeks glucose report.",
    "Get patient P015 information.",
    "Send P015's glucose report to the patient.",
    "Show the patient's glucose history for P015.",
    "Generate a report for P001.",
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 180px)', minHeight: '520px' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ padding: '8px', borderRadius: '10px', backgroundColor: 'rgba(14, 165, 233, 0.15)', color: 'var(--accent-primary)' }}>
            <Bot size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              LangGraph Clinical AI Orchestration
            </h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Deterministic Structured Tool Calling &bull; Zero DB Hallucinations
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--status-normal)', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '4px 10px', borderRadius: '9999px', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
          <Sparkles size={12} />
          <span>Active Agent</span>
        </div>
      </div>

      {/* Suggested prompts */}
      {errorMsg && (
        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', padding: '8px 12px', borderRadius: '8px', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
          {errorMsg}
        </div>
      )}
      <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            style={{
              whiteSpace: 'nowrap',
              fontSize: '0.75rem',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)',
              padding: '5px 12px',
              borderRadius: '9999px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
              e.currentTarget.style.color = 'var(--text-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-color)';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            "{p}"
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="glass-panel" style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem' }}>
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          const isSystem = m.sender === 'system';

          return (
            <div
              key={m.id}
              style={{
                display: 'flex',
                gap: '10px',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: '82%',
                flexDirection: isUser ? 'row-reverse' : 'row',
              }}
            >
              {/* Avatar */}
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  backgroundColor: isUser ? 'var(--accent-primary)' : isSystem ? '#ef4444' : 'rgba(14, 165, 233, 0.2)',
                  color: '#ffffff',
                }}
              >
                {isUser ? <User size={18} /> : isSystem ? <AlertCircle size={18} /> : <Bot size={18} />}
              </div>

              {/* Bubble */}
              <div>
                <div
                  style={{
                    padding: '12px 16px',
                    borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                    backgroundColor: isUser
                      ? 'rgba(14, 165, 233, 0.95)'
                      : isSystem
                      ? 'rgba(239, 68, 68, 0.15)'
                      : 'rgba(30, 41, 59, 0.85)',
                    color: isUser ? '#ffffff' : 'var(--text-primary)',
                    border: isUser ? 'none' : '1px solid var(--border-color)',
                    fontSize: '0.875rem',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {m.content}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: isUser ? 'right' : 'left' }}>
                  {m.timestamp}
                </div>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div style={{ display: 'flex', gap: '10px', alignSelf: 'flex-start', alignItems: 'center' }}>
            <div style={{ width: 34, height: 34, borderRadius: '50%', backgroundColor: 'rgba(14, 165, 233, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={18} color="var(--accent-primary)" />
            </div>
            <div style={{ padding: '10px 16px', borderRadius: '4px 16px 16px 16px', backgroundColor: 'rgba(30, 41, 59, 0.85)', border: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Terminal size={14} color="var(--accent-primary)" />
              <span>Orchestrating LangGraph tools...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        style={{ display: 'flex', gap: '0.75rem' }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a clinical question (e.g. 'Show P015's glucose report' or 'Send P015's report')..."
          style={{
            flex: 1,
            padding: '0.75rem 1.25rem',
            backgroundColor: 'rgba(17, 24, 39, 0.85)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-primary)',
            fontSize: '0.9rem',
            outline: 'none',
          }}
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '0.75rem 1.5rem',
            backgroundColor: 'var(--accent-primary)',
            color: '#ffffff',
            borderRadius: 'var(--radius-md)',
            fontWeight: 600,
            fontSize: '0.9rem',
            opacity: !input.trim() || isLoading ? 0.6 : 1,
            cursor: !input.trim() || isLoading ? 'not-allowed' : 'pointer',
          }}
        >
          <span>Send</span>
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
