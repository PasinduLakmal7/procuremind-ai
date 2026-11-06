import React, { useEffect, useState } from 'react';
import { supplierApi, SupplierItem } from '../services/api';
import { Plus, Building, Star, CheckCircle, Clock, X, Search } from 'lucide-react';

export const SuppliersPage: React.FC = () => {
  const [suppliers, setSuppliers] = useState<SupplierItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchCategory, setSearchCategory] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [companyName, setCompanyName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [city, setCity] = useState('Colombo');
  const [category, setCategory] = useState('Raw Materials');
  const [taxId, setTaxId] = useState('');
  const [tier, setTier] = useState('TIER_1');
  const [complianceStatus, setComplianceStatus] = useState('VERIFIED');
  const [rating, setRating] = useState('4.0');

  const fetchSuppliers = async () => {
    setLoading(true);
    try {
      const data = await supplierApi.list(searchCategory || undefined);
      setSuppliers(data);
    } catch (err: any) {
      console.error('Failed to load suppliers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, [searchCategory]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    try {
      await supplierApi.create({
        company_name: companyName,
        contact_email: contactEmail,
        contact_phone: contactPhone || undefined,
        city,
        country: 'Sri Lanka',
        category,
        tax_id: taxId || undefined,
        rating: parseFloat(rating) || 3.5,
        tier,
        compliance_status: complianceStatus,
      });
      setShowModal(false);
      // Reset form
      setCompanyName('');
      setContactEmail('');
      setContactPhone('');
      setTaxId('');
      fetchSuppliers();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error?.message || err.message || 'Failed to register supplier');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ margin: '0 0 6px 0', fontSize: '20px', color: '#0f172a' }}>Supplier Directory</h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
            Manage approved industrial suppliers, compliance records, and reliability tiers.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#0284c7',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            padding: '10px 16px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <Plus size={16} />
          <span>Register Supplier</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '20px', display: 'flex', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, backgroundColor: '#f8fafc', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
          <Search size={16} color="#94a3b8" />
          <input
            type="text"
            placeholder="Filter by product category (e.g. Steel, Electronics, Chemicals)..."
            value={searchCategory}
            onChange={(e) => setSearchCategory(e.target.value)}
            style={{ border: 'none', background: 'transparent', outline: 'none', width: '100%', fontSize: '14px' }}
          />
        </div>
      </div>

      {/* Supplier Table */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading suppliers...</div>
        ) : suppliers.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>
            <Building size={36} color="#94a3b8" style={{ marginBottom: '12px' }} />
            <p style={{ margin: '0 0 12px 0', fontSize: '15px' }}>No suppliers registered yet.</p>
            <button
              onClick={() => setShowModal(true)}
              style={{
                backgroundColor: '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                padding: '8px 16px',
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Add First Supplier
            </button>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                <th style={{ padding: '12px 16px' }}>Company Name</th>
                <th style={{ padding: '12px 16px' }}>Category</th>
                <th style={{ padding: '12px 16px' }}>Location</th>
                <th style={{ padding: '12px 16px' }}>Tier</th>
                <th style={{ padding: '12px 16px' }}>Rating</th>
                <th style={{ padding: '12px 16px' }}>Compliance</th>
                <th style={{ padding: '12px 16px' }}>Contact</th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((s) => (
                <tr key={s.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#0f172a' }}>{s.company_name}</td>
                  <td style={{ padding: '14px 16px', color: '#475569' }}>{s.category}</td>
                  <td style={{ padding: '14px 16px', color: '#475569' }}>{s.city}, {s.country}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '3px 8px',
                      borderRadius: '4px',
                      backgroundColor: s.tier === 'TIER_1' ? '#ecfdf5' : '#fef3c7',
                      color: s.tier === 'TIER_1' ? '#047857' : '#b45309',
                    }}>
                      {s.tier}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#d97706', fontWeight: 600 }}>
                      <Star size={14} fill="#f59e0b" color="#f59e0b" />
                      {s.rating.toFixed(1)}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '12px',
                      fontWeight: 600,
                      color: s.compliance_status === 'VERIFIED' ? '#16a34a' : '#ea580c',
                    }}>
                      {s.compliance_status === 'VERIFIED' ? <CheckCircle size={14} /> : <Clock size={14} />}
                      {s.compliance_status}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: '13px', color: '#64748b' }}>{s.contact_email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Registration Modal Dialog */}
      {showModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 50,
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            width: '100%',
            maxWidth: '520px',
            padding: '28px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>Register Industrial Supplier</h3>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            {errorMsg && (
              <div style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '10px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Company Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Colombo Industrial Tools PLC"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Corporate Email *</label>
                  <input
                    type="email"
                    required
                    placeholder="sales@supplier.lk"
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Contact Phone</label>
                  <input
                    type="text"
                    placeholder="+94 11 2345678"
                    value={contactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Category *</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  >
                    <option value="Raw Materials">Raw Materials (Steel, Rubber, etc.)</option>
                    <option value="Industrial Machinery">Industrial Machinery & Parts</option>
                    <option value="Electronics & Sensors">Electronics & Automation</option>
                    <option value="Packaging & Logistics">Packaging & Consumables</option>
                    <option value="Chemicals & Polymers">Chemicals & Polymers</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>City *</label>
                  <input
                    type="text"
                    required
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Tier</label>
                  <select
                    value={tier}
                    onChange={(e) => setTier(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                  >
                    <option value="TIER_1">Tier 1 (Prime)</option>
                    <option value="TIER_2">Tier 2 (Standard)</option>
                    <option value="TIER_3">Tier 3 (Alternative)</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Compliance</label>
                  <select
                    value={complianceStatus}
                    onChange={(e) => setComplianceStatus(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                  >
                    <option value="VERIFIED">Verified</option>
                    <option value="PENDING">Pending Audit</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Initial Rating</label>
                  <input
                    type="number"
                    step="0.1"
                    min="1"
                    max="5"
                    value={rating}
                    onChange={(e) => setRating(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  style={{ padding: '8px 16px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#f8fafc', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  style={{
                    padding: '8px 20px',
                    borderRadius: '6px',
                    border: 'none',
                    backgroundColor: '#0284c7',
                    color: '#ffffff',
                    fontWeight: 600,
                    cursor: submitting ? 'not-allowed' : 'pointer',
                  }}
                >
                  {submitting ? 'Registering...' : 'Save Supplier'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

