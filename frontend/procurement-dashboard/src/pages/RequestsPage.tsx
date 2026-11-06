import React, { useEffect, useState } from 'react';
import {
  procurementApi,
  supplierApi,
  PurchaseRequestItem,
  PurchaseRequestDetail,
  SupplierItem,
  LineItemPayload,
} from '../services/api';
import { Plus, ShoppingCart, X, Trash2, ArrowRight, Eye, UserPlus, CheckCircle2 } from 'lucide-react';

export const RequestsPage: React.FC = () => {
  const [requests, setRequests] = useState<PurchaseRequestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Detail Modal State
  const [selectedRequest, setSelectedRequest] = useState<PurchaseRequestDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Candidate Supplier State
  const [availableSuppliers, setAvailableSuppliers] = useState<SupplierItem[]>([]);
  const [selectedSupplierId, setSelectedSupplierId] = useState('');
  const [addingCandidate, setAddingCandidate] = useState(false);

  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Raw Materials');
  const [priority, setPriority] = useState('MEDIUM');
  const [budgetLimit, setBudgetLimit] = useState('');
  const [currency] = useState('LKR');
  const [items, setItems] = useState<LineItemPayload[]>([
    { item_name: '', quantity: 100, unit_of_measure: 'KG', target_unit_price: 2500 }
  ]);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const data = await procurementApi.listRequests();
      setRequests(data);
    } catch (err: any) {
      console.error('Failed to load purchase requests:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
    supplierApi.list().then(setAvailableSuppliers).catch(() => {});
  }, []);

  const handleAddItem = () => {
    setItems([...items, { item_name: '', quantity: 10, unit_of_measure: 'UNITS', target_unit_price: 1000 }]);
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleItemChange = (index: number, field: keyof LineItemPayload, value: any) => {
    const updated = [...items];
    (updated[index] as any)[field] = value;
    setItems(updated);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);

    const validItems = items.filter(it => it.item_name.trim().length > 0);

    try {
      await procurementApi.createRequest({
        title,
        description: description || undefined,
        category,
        priority,
        budget_limit: parseFloat(budgetLimit) || 0,
        currency,
        items: validItems.length > 0 ? validItems : undefined,
      });
      setShowModal(false);
      setTitle('');
      setDescription('');
      setBudgetLimit('');
      setItems([{ item_name: '', quantity: 100, unit_of_measure: 'KG', target_unit_price: 2500 }]);
      fetchRequests();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.error?.message || err.message || 'Failed to create request');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenDetail = async (requestId: string) => {
    setDetailLoading(true);
    try {
      const detail = await procurementApi.getRequestDetails(requestId);
      setSelectedRequest(detail);
    } catch (err: any) {
      console.error('Failed to load request details:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleSubmitDraft = async (requestId: string) => {
    try {
      await procurementApi.updateStatus(requestId, 'SUBMITTED');
      if (selectedRequest && selectedRequest.id === requestId) {
        handleOpenDetail(requestId);
      }
      fetchRequests();
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to submit request');
    }
  };

  const handleAddCandidate = async () => {
    if (!selectedRequest || !selectedSupplierId) return;
    const supp = availableSuppliers.find(s => s.id === selectedSupplierId);
    if (!supp) return;

    setAddingCandidate(true);
    try {
      await procurementApi.addCandidateSupplier(selectedRequest.id, {
        supplier_id: supp.id,
        supplier_name: supp.company_name,
        supplier_email: supp.contact_email,
      });
      handleOpenDetail(selectedRequest.id);
      setSelectedSupplierId('');
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to add candidate supplier');
    } finally {
      setAddingCandidate(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ margin: '0 0 6px 0', fontSize: '20px', color: '#0f172a' }}>Purchase Requests</h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
            Author requirements, line items, budget ceilings, candidate suppliers, and audit trail.
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
          <span>New Purchase Request</span>
        </button>
      </div>

      {/* Requests Table */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading purchase requests...</div>
        ) : requests.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>
            <ShoppingCart size={36} color="#94a3b8" style={{ marginBottom: '12px' }} />
            <p style={{ margin: '0 0 12px 0', fontSize: '15px' }}>No active purchase requests.</p>
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
              Create First Request
            </button>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                <th style={{ padding: '12px 16px' }}>Request #</th>
                <th style={{ padding: '12px 16px' }}>Title & Scope</th>
                <th style={{ padding: '12px 16px' }}>Category</th>
                <th style={{ padding: '12px 16px' }}>Priority</th>
                <th style={{ padding: '12px 16px' }}>Budget Ceiling</th>
                <th style={{ padding: '12px 16px' }}>Status</th>
                <th style={{ padding: '12px 16px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: '#0284c7' }}>{r.request_number}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ fontWeight: 600, color: '#0f172a' }}>{r.title}</div>
                    {r.description && <div style={{ fontSize: '12px', color: '#64748b' }}>{r.description}</div>}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#475569' }}>{r.category}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '3px 8px',
                      borderRadius: '4px',
                      backgroundColor: r.priority === 'HIGH' || r.priority === 'URGENT' ? '#fee2e2' : '#f1f5f9',
                      color: r.priority === 'HIGH' || r.priority === 'URGENT' ? '#b91c1c' : '#475569',
                    }}>
                      {r.priority}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#0f172a' }}>
                    {r.currency} {r.budget_limit.toLocaleString()}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      fontSize: '12px',
                      fontWeight: 600,
                      padding: '3px 10px',
                      borderRadius: '12px',
                      backgroundColor: r.status === 'APPROVED' ? '#dcfce7' : r.status === 'SUBMITTED' ? '#e0f2fe' : '#f1f5f9',
                      color: r.status === 'APPROVED' ? '#15803d' : r.status === 'SUBMITTED' ? '#0369a1' : '#475569',
                    }}>
                      {r.status}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <button
                      onClick={() => handleOpenDetail(r.id)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '12px',
                        padding: '6px 10px',
                        borderRadius: '4px',
                        border: '1px solid #cbd5e1',
                        backgroundColor: '#ffffff',
                        cursor: 'pointer',
                        color: '#0f172a',
                      }}
                    >
                      <Eye size={13} />
                      <span>Details</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Request Details Drawer/Modal */}
      {selectedRequest && (
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
          overflowY: 'auto',
          padding: '20px 0',
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            width: '100%',
            maxWidth: '750px',
            padding: '28px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            maxHeight: '90vh',
            overflowY: 'auto',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#0284c7' }}>{selectedRequest.request_number}</span>
                <h3 style={{ margin: '4px 0 0 0', fontSize: '18px', color: '#0f172a' }}>{selectedRequest.title}</h3>
                <span style={{
                  display: 'inline-block',
                  marginTop: '6px',
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '10px',
                  backgroundColor: selectedRequest.status === 'SUBMITTED' ? '#e0f2fe' : '#f1f5f9',
                  color: selectedRequest.status === 'SUBMITTED' ? '#0369a1' : '#475569',
                }}>
                  Status: {selectedRequest.status}
                </span>
              </div>
              <button onClick={() => setSelectedRequest(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            {/* Status Transition Action */}
            {selectedRequest.status === 'DRAFT' && (
              <div style={{ backgroundColor: '#f0f9ff', border: '1px solid #bae6fd', padding: '12px', borderRadius: '6px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '13px', color: '#0369a1' }}>
                  This request is currently in <strong>DRAFT</strong>. Submit to initiate supplier quotations.
                </div>
                <button
                  onClick={() => handleSubmitDraft(selectedRequest.id)}
                  style={{
                    backgroundColor: '#0284c7',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '6px 14px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Submit Request
                </button>
              </div>
            )}

            {/* Line Items */}
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#334155' }}>Line Items</h4>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', border: '1px solid #e2e8f0' }}>
                <thead style={{ backgroundColor: '#f8fafc', textAlign: 'left', color: '#64748b' }}>
                  <tr>
                    <th style={{ padding: '8px 12px' }}>Item Name</th>
                    <th style={{ padding: '8px 12px' }}>Quantity</th>
                    <th style={{ padding: '8px 12px' }}>Unit</th>
                    <th style={{ padding: '8px 12px' }}>Target Unit Price</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedRequest.items || []).map((it, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px 12px', fontWeight: 600 }}>{it.item_name}</td>
                      <td style={{ padding: '8px 12px' }}>{it.quantity}</td>
                      <td style={{ padding: '8px 12px' }}>{it.unit_of_measure}</td>
                      <td style={{ padding: '8px 12px' }}>{selectedRequest.currency} {it.target_unit_price || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Candidate Suppliers */}
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#334155' }}>Candidate Suppliers</h4>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                <select
                  value={selectedSupplierId}
                  onChange={(e) => setSelectedSupplierId(e.target.value)}
                  style={{ flex: 1, padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                >
                  <option value="">Select a registered supplier to invite...</option>
                  {availableSuppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.company_name} ({s.category} - {s.tier})
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleAddCandidate}
                  disabled={!selectedSupplierId || addingCandidate}
                  style={{
                    backgroundColor: '#0284c7',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '6px 14px',
                    fontSize: '12px',
                    cursor: !selectedSupplierId ? 'not-allowed' : 'pointer',
                  }}
                >
                  {addingCandidate ? 'Adding...' : 'Add Candidate'}
                </button>
              </div>

              {(selectedRequest.candidate_suppliers || []).length === 0 ? (
                <div style={{ fontSize: '13px', color: '#94a3b8', fontStyle: 'italic' }}>No candidate suppliers associated yet.</div>
              ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {selectedRequest.candidate_suppliers.map((cand) => (
                    <div
                      key={cand.id}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '12px',
                      }}
                    >
                      <strong>{cand.supplier_name}</strong> - <span style={{ color: '#0284c7' }}>{cand.invitation_status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Audit Trail */}
            <div>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#334155' }}>Audit History</h4>
              <div style={{ maxHeight: '140px', overflowY: 'auto', border: '1px solid #f1f5f9', borderRadius: '6px', padding: '8px' }}>
                {(selectedRequest.audit_events || []).map((ev) => (
                  <div key={ev.id} style={{ fontSize: '12px', color: '#64748b', padding: '4px 0', borderBottom: '1px solid #f8fafc' }}>
                    <strong style={{ color: '#0f172a' }}>{ev.event_type}</strong>: {ev.details}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Creation Modal */}
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
          overflowY: 'auto',
          padding: '20px 0',
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            width: '100%',
            maxWidth: '640px',
            padding: '28px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>Create Purchase Requirement</h3>
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
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Request Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mild Steel Billets 100x100mm Grade A"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Category *</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  >
                    <option value="Raw Materials">Raw Materials (Metals, Rubber, etc.)</option>
                    <option value="Industrial Machinery">Machinery & Heavy Equipment</option>
                    <option value="Electronics">Electrical & Electronics</option>
                    <option value="Chemicals">Industrial Chemicals & Gases</option>
                    <option value="Packaging">Packaging Materials</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  >
                    <option value="LOW">Low Priority</option>
                    <option value="MEDIUM">Medium Priority</option>
                    <option value="HIGH">High Priority</option>
                    <option value="URGENT">Urgent (Line Stoppage Risk)</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Budget Ceiling (LKR) *</label>
                <input
                  type="number"
                  required
                  min="0"
                  placeholder="e.g. 2500000"
                  value={budgetLimit}
                  onChange={(e) => setBudgetLimit(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>

              {/* Line Items Section */}
              <div style={{ marginBottom: '18px', borderTop: '1px solid #e2e8f0', paddingTop: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label style={{ fontSize: '13px', fontWeight: 600, color: '#334155' }}>Line Items</label>
                  <button
                    type="button"
                    onClick={handleAddItem}
                    style={{ fontSize: '12px', color: '#0284c7', background: 'none', border: 'none', fontWeight: 600, cursor: 'pointer' }}
                  >
                    + Add Item
                  </button>
                </div>

                {items.map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center' }}>
                    <input
                      type="text"
                      placeholder="Item specification"
                      value={item.item_name}
                      onChange={(e) => handleItemChange(idx, 'item_name', e.target.value)}
                      style={{ flex: 3, padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                    />
                    <input
                      type="number"
                      placeholder="Qty"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(idx, 'quantity', parseFloat(e.target.value) || 1)}
                      style={{ flex: 1, padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                    />
                    <input
                      type="text"
                      placeholder="Unit"
                      value={item.unit_of_measure}
                      onChange={(e) => handleItemChange(idx, 'unit_of_measure', e.target.value)}
                      style={{ flex: 1, padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                    />
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(idx)}
                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
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
                  {submitting ? 'Creating...' : 'Create Draft'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
