import React, { useEffect, useState } from 'react';
import { 
  procurementApi, 
  PurchaseRequestItem, 
  PurchaseRequestDetail, 
  ProcurementAuditEventItem 
} from '../services/api';
import { 
  History, 
  ShieldCheck, 
  FileCheck, 
  CheckCircle2, 
  Clock, 
  User, 
  AlertCircle 
} from 'lucide-react';

export const AuditCompliancePage: React.FC = () => {
  const [requests, setRequests] = useState<PurchaseRequestItem[]>([]);
  const [selectedRequestId, setSelectedRequestId] = useState('');
  const [requestDetail, setRequestDetail] = useState<PurchaseRequestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    const fetchReqs = async () => {
      setLoading(true);
      try {
        const data = await procurementApi.listRequests();
        setRequests(data);
        if (data.length > 0) setSelectedRequestId(data[0].id);
      } catch (err) {
        console.error('Failed to load requests for audit:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReqs();
  }, []);

  useEffect(() => {
    if (!selectedRequestId) return;
    setDetailLoading(true);
    procurementApi.getRequestDetails(selectedRequestId)
      .then((detail) => setRequestDetail(detail))
      .catch((err) => console.error('Failed to load audit detail:', err))
      .finally(() => setDetailLoading(false));
  }, [selectedRequestId]);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ margin: '0 0 6px 0', fontSize: '20px', color: '#0f172a' }}>
          Audit Trail & Statutory Compliance
        </h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
          Immutable procurement audit logging, human approval records, and Sri Lankan VAT compliance.
        </p>
      </div>

      {/* Compliance Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '28px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <ShieldCheck color="#16a34a" size={22} />
            <h3 style={{ margin: 0, fontSize: '15px', color: '#0f172a' }}>Human Governance Enforced</h3>
          </div>
          <p style={{ margin: 0, fontSize: '13px', color: '#475569' }}>
            Autonomous fund disbursement by AI agents is strictly blocked. All contractual awards require Human Procurement Manager sign-off.
          </p>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <FileCheck color="#0284c7" size={22} />
            <h3 style={{ margin: 0, fontSize: '15px', color: '#0f172a' }}>Sri Lankan VAT Compliance</h3>
          </div>
          <p style={{ margin: 0, fontSize: '13px', color: '#475569' }}>
            Quotations are automatically verified against the statutory 8% Value Added Tax standard before optimization ranking.
          </p>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <History color="#7c3aed" size={22} />
            <h3 style={{ margin: 0, fontSize: '15px', color: '#0f172a' }}>Reliable Transaction Outbox</h3>
          </div>
          <p style={{ margin: 0, fontSize: '13px', color: '#475569' }}>
            Every state machine transition and manager decision generates an immutable PostgreSQL outbox event dispatched to RabbitMQ.
          </p>
        </div>
      </div>

      {/* Audit Log Viewer */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <History size={20} color="#0f172a" />
            <h3 style={{ margin: 0, fontSize: '16px', color: '#0f172a' }}>
              Procurement Audit Log Explorer
            </h3>
          </div>
          <div>
            <select
              value={selectedRequestId}
              onChange={(e) => setSelectedRequestId(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
            >
              {requests.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.request_number} — {r.title} ({r.status})
                </option>
              ))}
            </select>
          </div>
        </div>

        {detailLoading ? (
          <div style={{ padding: '20px', color: '#64748b' }}>Loading audit events...</div>
        ) : requestDetail && requestDetail.audit_events && requestDetail.audit_events.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {requestDetail.audit_events.map((evt, idx) => (
              <div
                key={evt.id || idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '14px',
                  padding: '14px',
                  borderRadius: '6px',
                  border: '1px solid #f1f5f9',
                  backgroundColor: evt.event_type.startsWith('DECISION_') ? '#f0fdf4' : '#f8fafc',
                }}
              >
                <div style={{ marginTop: '2px' }}>
                  {evt.event_type.startsWith('DECISION_') ? (
                    <CheckCircle2 color="#16a34a" size={18} />
                  ) : (
                    <Clock color="#64748b" size={18} />
                  )}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '13px', color: '#0f172a' }}>
                      {evt.event_type}
                    </span>
                    <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                      {new Date(evt.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#475569', marginBottom: '4px' }}>
                    {evt.details}
                  </div>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: '#64748b' }}>
                    <span>Performed by: <code>{evt.performed_by}</code></span>
                    {evt.old_state && evt.new_state && (
                      <span>Transition: <strong>{evt.old_state}</strong> → <strong>{evt.new_state}</strong></span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>
            No audit events recorded for this purchase request yet.
          </div>
        )}
      </div>
    </div>
  );
};

