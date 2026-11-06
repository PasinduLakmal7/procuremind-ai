import React from 'react';
import { Clock } from 'lucide-react';

interface PlaceholderProps {
  title: string;
  stage: string;
  description: string;
}

export const PlaceholderPage: React.FC<PlaceholderProps> = ({ title, stage, description }) => {
  return (
    <div style={{
      backgroundColor: '#ffffff',
      borderRadius: '8px',
      padding: '48px',
      border: '1px solid #e2e8f0',
      textAlign: 'center',
      maxWidth: '600px',
      margin: '40px auto'
    }}>
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        backgroundColor: '#f8fafc',
        color: '#64748b',
        marginBottom: '16px'
      }}>
        <Clock size={28} />
      </div>
      <h2 style={{ margin: '0 0 8px 0', fontSize: '20px', color: '#0f172a' }}>{title}</h2>
      <div style={{
        display: 'inline-block',
        fontSize: '12px',
        fontWeight: 600,
        backgroundColor: '#fef3c7',
        color: '#92400e',
        padding: '4px 12px',
        borderRadius: '12px',
        marginBottom: '16px'
      }}>
        Scheduled for {stage}
      </div>
      <p style={{ margin: 0, fontSize: '14px', color: '#64748b', lineHeight: 1.6 }}>
        {description}
      </p>
    </div>
  );
};

