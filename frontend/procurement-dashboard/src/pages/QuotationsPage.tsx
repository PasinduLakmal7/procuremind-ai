import React, { useEffect, useState } from 'react';
import { 
  procurementApi, 
  supplierApi, 
  documentApi, 
  aiOrchestratorApi,
  PurchaseRequestItem, 
  SupplierItem, 
  QuotationItem, 
  DocumentItem,
  ExtractionResponse,
  WorkflowStatusResponse,
} from '../services/api';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  BrainCircuit, 
  X, 
  Edit3, 
  ArrowRight,
  ShieldAlert,
  Play
} from 'lucide-react';

export const QuotationsPage: React.FC = () => {
  const [requests, setRequests] = useState<PurchaseRequestItem[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierItem[]>([]);
  const [selectedRequestId, setSelectedRequestId] = useState<string>('');
  const [quotations, setQuotations] = useState<QuotationItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Form State
  const [selectedSupplierId, setSelectedSupplierId] = useState('');
  const [quoteNumber, setQuoteNumber] = useState('');
  const [totalCost, setTotalCost] = useState('');
  const [deliveryDays, setDeliveryDays] = useState('14');
  const [paymentTerms, setPaymentTerms] = useState('Net 30');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Extraction & Verification Modal
  const [activeDoc, setActiveDoc] = useState<DocumentItem | null>(null);
  const [extraction, setExtraction] = useState<ExtractionResponse | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [editSupplier, setEditSupplier] = useState('');
  const [editQuoteNo, setEditQuoteNo] = useState('');
  const [editTotal, setEditTotal] = useState('');

  // AI Workflow State
  const [workflowState, setWorkflowState] = useState<WorkflowStatusResponse | null>(null);
  const [runningWf, setRunningWf] = useState(false);

  // Human Procurement Decision State
  const [decisionReason, setDecisionReason] = useState('');
  const [deciding, setDeciding] = useState(false);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);

  const handleRecordDecision = async (action: 'APPROVE' | 'REJECT') => {
    if (!selectedRequestId) return;
    setDeciding(true);
    try {
      const winnerSupId = workflowState?.state?.recommendation?.winning_supplier_id;
      const winnerQuote = quotations.find(q => q.supplier_id === winnerSupId);
      await procurementApi.recordDecision(selectedRequestId, {
        action,
        decision_reason: decisionReason.trim() || (action === 'APPROVE' ? 'Approved based on AI multi-criteria recommendation.' : 'Rejected after procurement evaluation.'),
        selected_supplier_id: winnerSupId,
        selected_quotation_id: winnerQuote?.id,
      });
      setDecisionSuccess(`Purchase request successfully ${action}D with audit event logged.`);
      const updatedReqs = await procurementApi.listRequests();
      setRequests(updatedReqs);
      loadQuotationsAndDocs(selectedRequestId);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || err.message || 'Decision failed');
    } finally {
      setDeciding(false);
    }
  };

  // Load Requests and Suppliers
  useEffect(() => {
    const initData = async () => {
      try {
        const [reqs, sups] = await Promise.all([
          procurementApi.listRequests(),
          supplierApi.list(),
        ]);
        setRequests(reqs);
        setSuppliers(sups);
        if (reqs.length > 0) setSelectedRequestId(reqs[0].id);
        if (sups.length > 0) setSelectedSupplierId(sups[0].id);
      } catch (err) {
        console.error('Failed to load initial data:', err);
      }
    };
    initData();
  }, []);

  const loadQuotationsAndDocs = async (reqId: string) => {
    if (!reqId) return;
    setLoading(true);
    try {
      const [quotes, docs] = await Promise.all([
        procurementApi.listQuotations(reqId),
        documentApi.list(reqId),
      ]);
      setQuotations(quotes);
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load quotations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedRequestId) {
      loadQuotationsAndDocs(selectedRequestId);
    }
  }, [selectedRequestId]);

  const handleSubmitQuote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequestId || !selectedSupplierId) {
      setMessage({ text: 'Please select both a purchase request and a supplier.', type: 'error' });
      return;
    }

    setSubmitting(true);
    setMessage(null);

    try {
      let docId: string | undefined = undefined;

      if (uploadFile) {
        const docRecord = await documentApi.upload(uploadFile, selectedRequestId, selectedSupplierId);
        docId = docRecord.id;
      }

      await procurementApi.submitQuotation(selectedRequestId, {
        supplier_id: selectedSupplierId,
        quotation_number: quoteNumber,
        total_cost: parseFloat(totalCost),
        currency: 'LKR',
        estimated_delivery_days: parseInt(deliveryDays) || 14,
        payment_terms: paymentTerms,
        document_id: docId,
      });

      setMessage({ text: 'Quotation and document registered successfully!', type: 'success' });
      setQuoteNumber('');
      setTotalCost('');
      setUploadFile(null);
      loadQuotationsAndDocs(selectedRequestId);
    } catch (err: any) {
      setMessage({ text: err.response?.data?.error?.message || err.message || 'Submission failed', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  // Trigger Document Extraction
  const handleOpenIntelligence = async (doc: DocumentItem) => {
    setActiveDoc(doc);
    setExtraction(null);
    setWorkflowState(null);
    setExtracting(true);

    try {
      // First try to fetch existing extraction, else trigger
      let ext: ExtractionResponse;
      try {
        ext = await documentApi.getExtraction(doc.id);
      } catch {
        ext = await documentApi.triggerExtract(doc.id);
      }
      setExtraction(ext);
      setEditSupplier(ext.supplier_name || '');
      setEditQuoteNo(ext.quotation_number || '');
      setEditTotal(ext.total_cost ? ext.total_cost.toString() : '');
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to extract document intelligence');
    } finally {
      setExtracting(false);
    }
  };

  // Human Correction Save
  const handleSaveCorrections = async () => {
    if (!activeDoc || !extraction) return;
    setSavingEdit(true);
    try {
      const updated = await documentApi.correctExtraction(activeDoc.id, {
        supplier_name: editSupplier,
        quotation_number: editQuoteNo,
        total_cost: parseFloat(editTotal) || extraction.total_cost,
      });
      setExtraction(updated);
      alert('Extraction corrections saved with audit logging.');
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to save correction');
    } finally {
      setSavingEdit(false);
    }
  };

  // Human Verification Confirm
  const handleVerifyExtraction = async () => {
    if (!activeDoc) return;
    try {
      const verified = await documentApi.verifyExtraction(activeDoc.id);
      setExtraction(verified);
      loadQuotationsAndDocs(selectedRequestId);
      alert('Quotation extraction verified successfully.');
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to verify');
    }
  };

  // AI Workflow Start
  const handleStartWorkflow = async () => {
    if (!extraction) return;
    setRunningWf(true);
    try {
      const res = await aiOrchestratorApi.startWorkflow({
        purchase_request_id: selectedRequestId,
        document_id: extraction.document_id,
        supplier_id: extraction.supplier_id,
        extracted_data: extraction.structured_data,
        is_verified: extraction.is_verified,
      });
      setWorkflowState(res);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to start AI workflow');
    } finally {
      setRunningWf(false);
    }
  };

  // AI Workflow Resume
  const handleResumeWorkflow = async () => {
    if (!workflowState || !extraction) return;
    setRunningWf(true);
    try {
      const res = await aiOrchestratorApi.resumeWorkflow(workflowState.workflow_id, {
        updated_extracted_data: extraction.structured_data,
        confirm_human_verification: true,
      });
      setWorkflowState(res);
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to resume AI workflow');
    } finally {
      setRunningWf(false);
    }
  };

  const getSupplierName = (supId: string) => {
    const s = suppliers.find(item => item.id === supId);
    return s ? s.company_name : 'Registered Vendor';
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ margin: '0 0 6px 0', fontSize: '20px', color: '#0f172a' }}>Quotations, Document AI & Orchestration</h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
          Upload supplier quotations, extract structured line items, review OCR confidence, verify evidence, and coordinate multi-agent AI.
        </p>
      </div>

      {/* Active PR Selector */}
      <div style={{ backgroundColor: '#ffffff', padding: '16px 20px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
          Select Active Purchase Requirement
        </label>
        <select
          value={selectedRequestId}
          onChange={(e) => setSelectedRequestId(e.target.value)}
          style={{ width: '100%', maxWidth: '480px', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', fontWeight: 500 }}
        >
          {requests.map((r) => (
            <option key={r.id} value={r.id}>
              {r.request_number} — {r.title} ({r.currency} {r.budget_limit.toLocaleString()})
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '24px' }}>
        {/* Left Column: Proposals and Uploaded Documents with AI Actions */}
        <div>
          <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden', marginBottom: '24px' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '16px', color: '#0f172a' }}>Quotation Documents & AI Analysis</h3>
              <span style={{ fontSize: '12px', color: '#64748b' }}>{documents.length} files</span>
            </div>

            {loading ? (
              <div style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>Loading documents...</div>
            ) : documents.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                <FileText size={36} color="#94a3b8" style={{ marginBottom: '12px' }} />
                <p style={{ margin: 0, fontSize: '14px' }}>No documents uploaded yet for this requirement.</p>
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                    <th style={{ padding: '10px 14px' }}>File Name</th>
                    <th style={{ padding: '10px 14px' }}>Size</th>
                    <th style={{ padding: '10px 14px' }}>Status</th>
                    <th style={{ padding: '10px 14px' }}>AI Intelligence</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((d) => (
                    <tr key={d.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 600, color: '#0f172a' }}>{d.file_name}</td>
                      <td style={{ padding: '12px 14px', color: '#64748b' }}>{(d.file_size / 1024).toFixed(1)} KB</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '10px',
                          backgroundColor: d.status === 'VERIFIED' ? '#dcfce7' : d.status === 'EXTRACTED' ? '#e0f2fe' : '#f1f5f9',
                          color: d.status === 'VERIFIED' ? '#15803d' : d.status === 'EXTRACTED' ? '#0369a1' : '#475569',
                        }}>
                          {d.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <button
                          onClick={() => handleOpenIntelligence(d)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            backgroundColor: '#0284c7',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '4px',
                            padding: '6px 12px',
                            fontSize: '12px',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          <BrainCircuit size={14} />
                          <span>Review & Verify AI</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Right Column: Register Quotation Form */}
        <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#0f172a' }}>Submit Quotation & Document</h3>

          {message && (
            <div style={{
              backgroundColor: message.type === 'success' ? '#ecfdf5' : '#fee2e2',
              color: message.type === 'success' ? '#047857' : '#b91c1c',
              padding: '10px',
              borderRadius: '6px',
              fontSize: '13px',
              marginBottom: '16px',
            }}>
              {message.text}
            </div>
          )}

          <form onSubmit={handleSubmitQuote}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Supplier *</label>
              <select
                required
                value={selectedSupplierId}
                onChange={(e) => setSelectedSupplierId(e.target.value)}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
              >
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>{s.company_name} ({s.category})</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Quotation # *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. QUO-2026-042"
                  value={quoteNumber}
                  onChange={(e) => setQuoteNumber(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Total Price (LKR) *</label>
                <input
                  type="number"
                  required
                  min="0"
                  placeholder="e.g. 1450000"
                  value={totalCost}
                  onChange={(e) => setTotalCost(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>
                Quotation File (PDF, XLSX, CSV, PNG)
              </label>
              <div style={{ border: '2px dashed #cbd5e1', borderRadius: '6px', padding: '16px', textAlign: 'center', backgroundColor: '#f8fafc' }}>
                <UploadCloud size={28} color="#0284c7" style={{ marginBottom: '4px' }} />
                <input
                  type="file"
                  accept=".pdf,.xlsx,.xls,.csv,.png,.jpg"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  style={{ display: 'block', width: '100%', fontSize: '12px' }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: submitting ? 'not-allowed' : 'pointer',
              }}
            >
              {submitting ? 'Uploading & Registering...' : 'Upload & Register Quotation'}
            </button>
          </form>
        </div>
      </div>

      {/* Document Intelligence & Human Verification Modal */}
      {activeDoc && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 50,
          overflowY: 'auto',
          padding: '24px 0',
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            width: '100%',
            maxWidth: '820px',
            padding: '28px',
            maxHeight: '92vh',
            overflowY: 'auto',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#0284c7' }}>DOCUMENT AI EXTRACTION & REVIEW</span>
                <h3 style={{ margin: '4px 0 0 0', fontSize: '18px', color: '#0f172a' }}>{activeDoc.file_name}</h3>
              </div>
              <button onClick={() => setActiveDoc(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            {extracting ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                <BrainCircuit size={36} color="#0284c7" style={{ marginBottom: '12px' }} />
                <p>Executing Document Intelligence extraction pipeline...</p>
              </div>
            ) : extraction ? (
              <div>
                {/* Confidence & Verification Status Bar */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px' }}>
                  <div style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>EXTRACTION CONFIDENCE</div>
                    <div style={{ fontSize: '18px', fontWeight: 700, color: extraction.overall_confidence >= 0.85 ? '#16a34a' : '#d97706' }}>
                      {(extraction.overall_confidence * 100).toFixed(0)}%
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>ARITHMETIC CONSISTENCY</div>
                    <div style={{ fontSize: '15px', fontWeight: 700, color: extraction.arithmetic_valid ? '#16a34a' : '#dc2626', marginTop: '2px' }}>
                      {extraction.arithmetic_valid ? 'Verified Consistent' : 'Mismatch Detected'}
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>HUMAN VERIFICATION</div>
                    <div style={{ fontSize: '15px', fontWeight: 700, color: extraction.is_verified ? '#16a34a' : '#475569', marginTop: '2px' }}>
                      {extraction.is_verified ? 'Confirmed' : 'Pending Review'}
                    </div>
                  </div>
                </div>

                {/* Flagged Warnings or Security Alerts */}
                {extraction.flagged_reasons.length > 0 && (
                  <div style={{ backgroundColor: '#fffbeb', border: '1px solid #fef3c7', borderRadius: '6px', padding: '12px', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, color: '#b45309', fontSize: '13px', marginBottom: '6px' }}>
                      <AlertTriangle size={16} />
                      <span>Review Flags Detected:</span>
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#92400e' }}>
                      {extraction.flagged_reasons.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Editable Extracted Fields */}
                <div style={{ marginBottom: '20px', backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#0f172a' }}>Editable Structured Quotation</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#475569', fontWeight: 600, marginBottom: '4px' }}>Supplier Name</label>
                      <input
                        type="text"
                        value={editSupplier}
                        onChange={(e) => setEditSupplier(e.target.value)}
                        style={{ width: '100%', padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#475569', fontWeight: 600, marginBottom: '4px' }}>Quote Ref #</label>
                      <input
                        type="text"
                        value={editQuoteNo}
                        onChange={(e) => setEditQuoteNo(e.target.value)}
                        style={{ width: '100%', padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#475569', fontWeight: 600, marginBottom: '4px' }}>Total Cost (LKR)</label>
                      <input
                        type="number"
                        value={editTotal}
                        onChange={(e) => setEditTotal(e.target.value)}
                        style={{ width: '100%', padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                      />
                    </div>
                  </div>

                  <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                    <button
                      onClick={handleSaveCorrections}
                      disabled={savingEdit}
                      style={{
                        padding: '6px 14px',
                        backgroundColor: '#ffffff',
                        border: '1px solid #cbd5e1',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      {savingEdit ? 'Saving...' : 'Save Field Edits'}
                    </button>
                    {!extraction.is_verified && (
                      <button
                        onClick={handleVerifyExtraction}
                        style={{
                          padding: '6px 14px',
                          backgroundColor: '#16a34a',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        Confirm & Verify Extraction
                      </button>
                    )}
                  </div>
                </div>

                {/* Line Items Table */}
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#0f172a' }}>Extracted Line Items</h4>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', border: '1px solid #e2e8f0' }}>
                    <thead style={{ backgroundColor: '#f8fafc', textAlign: 'left', color: '#64748b' }}>
                      <tr>
                        <th style={{ padding: '8px 12px' }}>Description</th>
                        <th style={{ padding: '8px 12px' }}>Qty</th>
                        <th style={{ padding: '8px 12px' }}>Unit</th>
                        <th style={{ padding: '8px 12px' }}>Unit Price</th>
                        <th style={{ padding: '8px 12px' }}>Total Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(extraction.structured_data.line_items || []).map((it, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '8px 12px', fontWeight: 600 }}>{it.item_name}</td>
                          <td style={{ padding: '8px 12px' }}>{it.quantity}</td>
                          <td style={{ padding: '8px 12px' }}>{it.unit_of_measure}</td>
                          <td style={{ padding: '8px 12px' }}>LKR {it.unit_price.toLocaleString()}</td>
                          <td style={{ padding: '8px 12px', fontWeight: 600 }}>LKR {it.total_price.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Multi-Agent Orchestrator Trigger & Progress */}
                <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div>
                      <h4 style={{ margin: '0 0 2px 0', fontSize: '14px', color: '#0f172a' }}>LangGraph Multi-Agent Orchestration</h4>
                      <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
                        Evaluates extraction, verifies compliance, benchmarks against budget, and drafts decision recommendation.
                      </p>
                    </div>
                    {!workflowState ? (
                      <button
                        onClick={handleStartWorkflow}
                        disabled={runningWf}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          backgroundColor: '#0284c7',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '8px 16px',
                          fontSize: '13px',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        <Play size={14} />
                        <span>{runningWf ? 'Evaluating...' : 'Run AI Workflow'}</span>
                      </button>
                    ) : workflowState.status === 'WAITING_FOR_HUMAN_REVIEW' ? (
                      <button
                        onClick={handleResumeWorkflow}
                        disabled={runningWf}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          backgroundColor: '#d97706',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '8px 16px',
                          fontSize: '13px',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        <ArrowRight size={14} />
                        <span>Resume AI Workflow</span>
                      </button>
                    ) : null}
                  </div>

                  {workflowState && (
                    <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '12px', fontSize: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <span style={{ fontWeight: 600, color: '#166534' }}>Workflow Status: {workflowState.status}</span>
                          <span style={{ color: '#166534' }}>Current Step: {workflowState.current_step}</span>
                        </div>
                        {workflowState.human_review_reason && (
                          <div style={{ color: '#b45309', marginBottom: '6px' }}>
                            <strong>Paused for Review:</strong> {workflowState.human_review_reason}
                          </div>
                        )}
                      </div>

                      {/* Stage 4: Risk Prediction Profile */}
                      {workflowState.state.risk_assessment && (
                        <div style={{ border: '1px solid #e2e8f0', borderRadius: '6px', padding: '12px', backgroundColor: '#ffffff' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 600, fontSize: '13px', color: '#0f172a' }}>Supplier Risk Assessment</span>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontSize: '11px',
                              fontWeight: 700,
                              backgroundColor: workflowState.state.risk_assessment.supplier_risk_tier === 'LOW' ? '#dcfce7' :
                                               workflowState.state.risk_assessment.supplier_risk_tier === 'MEDIUM' ? '#fef9c3' :
                                               workflowState.state.risk_assessment.supplier_risk_tier === 'INSUFFICIENT_DATA' ? '#f1f5f9' : '#fee2e2',
                              color: workflowState.state.risk_assessment.supplier_risk_tier === 'LOW' ? '#166534' :
                                     workflowState.state.risk_assessment.supplier_risk_tier === 'MEDIUM' ? '#854d0e' :
                                     workflowState.state.risk_assessment.supplier_risk_tier === 'INSUFFICIENT_DATA' ? '#475569' : '#991b1b',
                            }}>
                              TIER: {workflowState.state.risk_assessment.supplier_risk_tier}
                            </span>
                          </div>
                          <p style={{ margin: '0 0 6px 0', fontSize: '12px', color: '#475569' }}>
                            {workflowState.state.risk_assessment.explanation}
                          </p>
                          <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: '#64748b' }}>
                            <span>Observations: {workflowState.state.risk_assessment.observation_count}</span>
                            <span>Confidence: {(workflowState.state.risk_assessment.confidence * 100).toFixed(0)}%</span>
                            <span>Model: {workflowState.state.risk_assessment.model_version}</span>
                          </div>
                        </div>
                      )}

                      {/* Stage 4: Multi-Criteria Optimization Rankings */}
                      {workflowState.state.optimization?.rankings && (
                        <div style={{ border: '1px solid #e2e8f0', borderRadius: '6px', padding: '12px', backgroundColor: '#ffffff' }}>
                          <span style={{ fontWeight: 600, fontSize: '13px', color: '#0f172a', display: 'block', marginBottom: '8px' }}>
                            MCDA Quotation Optimization (Weights: Cost 40%, Delivery 25%, Quality 20%, Reliability 15%)
                          </span>
                          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                            <thead>
                              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                                <th style={{ padding: '6px' }}>Rank</th>
                                <th style={{ padding: '6px' }}>Supplier</th>
                                <th style={{ padding: '6px' }}>Cost</th>
                                <th style={{ padding: '6px' }}>Lead Time</th>
                                <th style={{ padding: '6px' }}>Composite Score</th>
                                <th style={{ padding: '6px' }}>Status</th>
                              </tr>
                            </thead>
                            <tbody>
                              {workflowState.state.optimization.rankings.map((r: any, idx: number) => (
                                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', backgroundColor: r.rank === 1 && r.is_eligible ? '#f0fdf4' : 'transparent' }}>
                                  <td style={{ padding: '6px', fontWeight: 600 }}>#{r.rank}</td>
                                  <td style={{ padding: '6px', fontWeight: 600 }}>{r.supplier_name}</td>
                                  <td style={{ padding: '6px' }}>LKR {r.total_cost?.toLocaleString()}</td>
                                  <td style={{ padding: '6px' }}>{r.lead_time_days} days</td>
                                  <td style={{ padding: '6px', fontWeight: 700, color: r.is_eligible ? '#0f766e' : '#94a3b8' }}>
                                    {r.is_eligible ? r.composite_score.toFixed(4) : 'N/A'}
                                  </td>
                                  <td style={{ padding: '6px' }}>
                                    <span style={{
                                      padding: '2px 6px',
                                      borderRadius: '4px',
                                      fontSize: '10px',
                                      fontWeight: 600,
                                      backgroundColor: r.is_eligible ? '#dcfce7' : '#fee2e2',
                                      color: r.is_eligible ? '#166534' : '#991b1b',
                                    }}>
                                      {r.is_eligible ? 'ELIGIBLE' : 'DISQUALIFIED'}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {/* Stage 4: Explainable AI Rationale */}
                      {workflowState.state.explainability_report && (
                        <div style={{ border: '1px solid #e0e7ff', borderRadius: '6px', padding: '12px', backgroundColor: '#f5f3ff', fontSize: '12px' }}>
                          <span style={{ fontWeight: 600, fontSize: '13px', color: '#4338ca', display: 'block', marginBottom: '6px' }}>
                            Explainable AI Procurement Rationale
                          </span>
                          <p style={{ margin: '0 0 6px 0', color: '#3730a3' }}>
                            {workflowState.state.explainability_report.top_supplier_rationale}
                          </p>
                          {workflowState.state.explainability_report.excluded_suppliers_rationale?.length > 0 && (
                            <div style={{ marginTop: '6px', color: '#6b21a8' }}>
                              <strong>Exclusions:</strong>
                              <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                                {workflowState.state.explainability_report.excluded_suppliers_rationale.map((r: string, i: number) => (
                                  <li key={i}>{r}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          <div style={{ marginTop: '6px', fontSize: '11px', color: '#6366f1' }}>
                            Statutory Check: Sri Lankan 8% VAT Compliant | Risk Method: {workflowState.state.explainability_report.risk_method}
                          </div>
                        </div>
                      )}

                      {/* Stage 4: Human Procurement Decision Gate */}
                      {workflowState.state.recommendation && (
                        <div style={{ border: '2px solid #0284c7', borderRadius: '6px', padding: '14px', backgroundColor: '#f0f9ff' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 700, fontSize: '14px', color: '#0369a1' }}>
                              Human Procurement Decision Gate
                            </span>
                            <span style={{ fontSize: '12px', color: '#0284c7', fontWeight: 600 }}>
                              Award Recommendation: {workflowState.state.recommendation.winning_supplier_name || 'Primary Vendor'}
                            </span>
                          </div>
                          <p style={{ margin: '0 0 10px 0', fontSize: '11px', color: '#0c4a6e' }}>
                            {workflowState.state.recommendation.governance_notice}
                          </p>

                          {decisionSuccess ? (
                            <div style={{ backgroundColor: '#dcfce7', border: '1px solid #86efac', borderRadius: '4px', padding: '8px', color: '#166534', fontWeight: 600, fontSize: '12px' }}>
                              ✓ {decisionSuccess}
                            </div>
                          ) : (
                            <div>
                              <textarea
                                value={decisionReason}
                                onChange={(e) => setDecisionReason(e.target.value)}
                                placeholder="Enter auditable procurement decision justification notes..."
                                rows={2}
                                style={{ width: '100%', boxSizing: 'border-box', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '8px', fontSize: '12px', marginBottom: '10px' }}
                              />
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                  onClick={() => handleRecordDecision('APPROVE')}
                                  disabled={deciding}
                                  style={{
                                    backgroundColor: '#16a34a',
                                    color: '#ffffff',
                                    border: 'none',
                                    borderRadius: '4px',
                                    padding: '8px 16px',
                                    fontSize: '12px',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                  }}
                                >
                                  {deciding ? 'Recording...' : '✓ Approve Procurement Award'}
                                </button>
                                <button
                                  onClick={() => handleRecordDecision('REJECT')}
                                  disabled={deciding}
                                  style={{
                                    backgroundColor: '#dc2626',
                                    color: '#ffffff',
                                    border: 'none',
                                    borderRadius: '4px',
                                    padding: '8px 16px',
                                    fontSize: '12px',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                  }}
                                >
                                  {deciding ? 'Recording...' : '✕ Reject Award'}
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
