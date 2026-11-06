import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, LogIn } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuickFill = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('DemoPassword123!');
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#0f172a',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        padding: '36px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: '#0284c7',
            color: '#ffffff',
            marginBottom: '12px'
          }}>
            <ShieldCheck size={28} />
          </div>
          <h2 style={{ margin: '0 0 6px 0', fontSize: '22px', fontWeight: 700, color: '#0f172a' }}>
            Procurement Intelligence
          </h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
            Explainable Multi-Agent AI Decision Support
          </p>
        </div>

        {errorMessage && (
          <div style={{
            backgroundColor: '#fee2e2',
            color: '#b91c1c',
            padding: '12px',
            borderRadius: '6px',
            fontSize: '13px',
            marginBottom: '20px'
          }}>
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
              Corporate Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="officer@factory.lk"
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '10px 14px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '14px',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '10px 14px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '14px',
                outline: 'none',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: submitting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              opacity: submitting ? 0.7 : 1,
            }}
          >
            <LogIn size={16} />
            <span>{submitting ? 'Authenticating...' : 'Sign In'}</span>
          </button>
        </form>

        {/* Demo Fast Fill helpers */}
        <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
          <p style={{ margin: '0 0 10px 0', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Demo Accounts (Development)
          </p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => handleQuickFill('officer@colombosteel.lk')}
              style={{
                fontSize: '11px',
                padding: '4px 8px',
                backgroundColor: '#f1f5f9',
                border: '1px solid #cbd5e1',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Procurement Officer
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('manager@colombosteel.lk')}
              style={{
                fontSize: '11px',
                padding: '4px 8px',
                backgroundColor: '#f1f5f9',
                border: '1px solid #cbd5e1',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Manager
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

