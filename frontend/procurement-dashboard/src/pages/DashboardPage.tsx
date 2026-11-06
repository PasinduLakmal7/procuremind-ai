import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { procurementApi, supplierApi, PurchaseRequestItem } from '../services/api';
import { 
  Server, 
  CheckCircle2, 
  AlertTriangle, 
  Layers, 
  Cpu, 
  Database, 
  ShoppingCart, 
  Users, 
  Clock, 
  Award,
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';

interface ServiceHealth {
  name: string;
  port: number;
  status: 'online' | 'offline' | 'checking';
}

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [requests, setRequests] = useState<PurchaseRequestItem[]>([]);
  const [supplierCount, setSupplierCount] = useState(0);
  const [loadingData, setLoadingData] = useState(true);

  const [services, setServices] = useState<ServiceHealth[]>([
    { name: 'identity-service', port: 8001, status: 'checking' },
    { name: 'procurement-service', port: 8002, status: 'checking' },
    { name: 'supplier-service', port: 8003, status: 'checking' },
    { name: 'document-service', port: 8004, status: 'checking' },
    { name: 'ai-orchestrator-service', port: 8005, status: 'checking' },
    { name: 'risk-service', port: 8006, status: 'checking' },
    { name: 'optimization-service', port: 8007, status: 'checking' },
  ]);

  useEffect(() => {
    // Probe backend microservices
    const checkHealth = async () => {
      const updated = await Promise.all(
        services.map(async (svc) => {
          try {
            await axios.get(`/api/v1/${svc.name.replace('-service', '')}/health`, { timeout: 1500 });
            return { ...svc, status: 'online' as const };
          } catch {
            return { ...svc, status: 'offline' as const };
          }
        })
      );
      setServices(updated);
    };

    const loadMetrics = async () => {
      setLoadingData(true);
      try {
        const [reqs, sups] = await Promise.all([
          procurementApi.listRequests().catch(() => []),
          supplierApi.list().catch(() => []),
        ]);
        setRequests(reqs);
        setSupplierCount(sups.length);
      } finally {
        setLoadingData(false);
      }
    };

    checkHealth();
    loadMetrics();
  }, []);

  const pendingCount = requests.filter((r) => r.status === 'SUBMITTED' || r.status === 'UNDER_EVALUATION').length;
  const approvedCount = requests.filter((r) => r.status === 'APPROVED').length;
  const draftCount = requests.filter((r) => r.status === 'DRAFT').length;

  return (
    <div>
      {/* Welcome Card */}
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        padding: '24px',
        border: '1px solid #e2e8f0',
        marginBottom: '24px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '20px', color: '#0f172a' }}>
              Welcome back, {user?.full_name}!
            </h2>
            <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
              Organization: <strong>{user?.organization_name || user?.organization_id}</strong>
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {user?.roles?.map((role) => (
              <span
                key={role}
                style={{
                  fontSize: '12px',
                  padding: '4px 10px',
                  backgroundColor: '#dbeafe',
                  color: '#1e40af',
                  borderRadius: '9999px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                }}
              >
                {role.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Real Procurement KPI Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Total Requests</span>
            <ShoppingCart size={18} color="#0284c7" />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }}>
            {loadingData ? '...' : requests.length}
          </div>
          <span style={{ fontSize: '11px', color: '#64748b' }}>{draftCount} in Draft status</span>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Pending Review</span>
            <Clock size={18} color="#d97706" />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#d97706' }}>
            {loadingData ? '...' : pendingCount}
          </div>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Awaiting Manager evaluation</span>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Approved Awards</span>
            <Award size={18} color="#16a34a" />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#16a34a' }}>
            {loadingData ? '...' : approvedCount}
          </div>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Contractual commitment finalized</span>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Vendors Directory</span>
            <Users size={18} color="#7c3aed" />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a' }}>
            {loadingData ? '...' : supplierCount}
          </div>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Registered industrial suppliers</span>
        </div>
      </div>

      {/* Recent Procurement Activity */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ margin: 0, fontSize: '16px', color: '#0f172a' }}>Recent Purchase Requests</h3>
          <Link to="/requests" style={{ fontSize: '12px', color: '#0284c7', textDecoration: 'none', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
            View all <ArrowRight size={14} />
          </Link>
        </div>
        {requests.length === 0 ? (
          <div style={{ padding: '16px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
            No purchase requests recorded yet. Create one in the Purchase Requests tab.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#64748b', backgroundColor: '#f8fafc' }}>
                <th style={{ padding: '8px 12px' }}>Request #</th>
                <th style={{ padding: '8px 12px' }}>Title</th>
                <th style={{ padding: '8px 12px' }}>Category</th>
                <th style={{ padding: '8px 12px' }}>Budget Limit</th>
                <th style={{ padding: '8px 12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {requests.slice(0, 5).map((r) => (
                <tr key={r.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 600 }}>{r.request_number}</td>
                  <td style={{ padding: '10px 12px' }}>{r.title}</td>
                  <td style={{ padding: '10px 12px', color: '#64748b' }}>{r.category}</td>
                  <td style={{ padding: '10px 12px' }}>{r.currency} {r.budget_limit?.toLocaleString()}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: 600,
                      backgroundColor: r.status === 'APPROVED' ? '#dcfce7' :
                                       r.status === 'SUBMITTED' ? '#dbeafe' :
                                       r.status === 'REJECTED' ? '#fee2e2' : '#f1f5f9',
                      color: r.status === 'APPROVED' ? '#166534' :
                             r.status === 'SUBMITTED' ? '#1e40af' :
                             r.status === 'REJECTED' ? '#991b1b' : '#475569',
                    }}>
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Services Health Check Table */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
          <Server size={18} color="#0f172a" />
          <h3 style={{ margin: 0, fontSize: '15px', color: '#0f172a' }}>
            Microservices Health Status Probes
          </h3>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
              <th style={{ padding: '8px 12px' }}>Microservice</th>
              <th style={{ padding: '8px 12px' }}>Port</th>
              <th style={{ padding: '8px 12px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {services.map((svc) => (
              <tr key={svc.name} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '8px 12px', fontWeight: 500, color: '#1e293b' }}>{svc.name}</td>
                <td style={{ padding: '8px 12px', color: '#64748b' }}>:{svc.port}</td>
                <td style={{ padding: '8px 12px' }}>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12px',
                    fontWeight: 500,
                    color: svc.status === 'online' ? '#16a34a' : '#d97706',
                  }}>
                    {svc.status === 'online' ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
                    {svc.status.toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
