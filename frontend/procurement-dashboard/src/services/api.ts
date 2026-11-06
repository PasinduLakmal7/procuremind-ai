import axios, { AxiosError } from 'axios';
import { ApiResponse, AuthTokens, UserProfile } from '../types/auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auto-inject Authorization header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for 401 handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ----------------- Auth API -----------------
export const authApi = {
  login: async (email: string, password: string): Promise<AuthTokens> => {
    const res = await apiClient.post<ApiResponse<AuthTokens>>('/api/v1/identity/auth/login', {
      email,
      password,
    });
    return res.data.data;
  },

  getCurrentUser: async (): Promise<UserProfile> => {
    const res = await apiClient.get<ApiResponse<UserProfile>>('/api/v1/identity/auth/me');
    return res.data.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    try {
      await apiClient.post('/api/v1/identity/auth/logout', { refresh_token: refreshToken });
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },
};

// ----------------- Supplier API -----------------
export interface SupplierItem {
  id: string;
  company_name: string;
  contact_email: string;
  contact_phone?: string;
  address?: string;
  city: string;
  country: string;
  category: string;
  tax_id?: string;
  rating: number;
  tier: string;
  compliance_status: string;
  is_active: boolean;
  created_at: string;
}

export const supplierApi = {
  list: async (category?: string): Promise<SupplierItem[]> => {
    const params = category ? { category } : {};
    const res = await apiClient.get<ApiResponse<SupplierItem[]>>('/api/v1/supplier/suppliers', { params });
    return res.data.data;
  },

  create: async (payload: Omit<SupplierItem, 'id' | 'is_active' | 'created_at'>): Promise<SupplierItem> => {
    const res = await apiClient.post<ApiResponse<SupplierItem>>('/api/v1/supplier/suppliers', payload);
    return res.data.data;
  },
};

// ----------------- Procurement API -----------------
export interface LineItemPayload {
  item_name: string;
  specification?: string;
  quantity: number;
  unit_of_measure: string;
  target_unit_price?: number;
}

export interface CandidateSupplierItem {
  id: string;
  supplier_id: string;
  supplier_name: string;
  supplier_email?: string;
  invitation_status: string;
  invited_at: string;
}

export interface PurchaseRequestItem {
  id: string;
  organization_id: string;
  created_by_user_id: string;
  request_number: string;
  title: string;
  description?: string;
  category: string;
  priority: string;
  budget_limit: number;
  currency: string;
  required_delivery_date?: string;
  status: string;
  items?: LineItemPayload[];
  created_at: string;
}

export interface ProcurementAuditEventItem {
  id: string;
  purchase_request_id: string;
  event_type: string;
  performed_by: string;
  old_state?: string;
  new_state?: string;
  details?: string;
  created_at: string;
}

export interface PurchaseRequestDetail extends PurchaseRequestItem {
  candidate_suppliers: CandidateSupplierItem[];
  audit_events: ProcurementAuditEventItem[];
}

export interface QuotationItem {
  id: string;
  organization_id: string;
  purchase_request_id: string;
  supplier_id: string;
  quotation_number: string;
  version: number;
  total_cost: number;
  currency: string;
  validity_date?: string;
  estimated_delivery_days: number;
  warranty_terms?: string;
  payment_terms?: string;
  status: string;
  document_id?: string;
  created_at: string;
}

export const procurementApi = {
  listRequests: async (status?: string): Promise<PurchaseRequestItem[]> => {
    const params = status ? { status } : {};
    const res = await apiClient.get<ApiResponse<PurchaseRequestItem[]>>('/api/v1/procurement/requests', { params });
    return res.data.data;
  },

  createRequest: async (payload: {
    title: string;
    description?: string;
    category: string;
    priority: string;
    budget_limit: number;
    currency: string;
    items?: LineItemPayload[];
  }): Promise<PurchaseRequestItem> => {
    const res = await apiClient.post<ApiResponse<PurchaseRequestItem>>('/api/v1/procurement/requests', payload);
    return res.data.data;
  },

  getRequestDetails: async (requestId: string): Promise<PurchaseRequestDetail> => {
    const res = await apiClient.get<ApiResponse<PurchaseRequestDetail>>(`/api/v1/procurement/requests/${requestId}/details`);
    return res.data.data;
  },

  updateStatus: async (requestId: string, status: string): Promise<PurchaseRequestItem> => {
    const res = await apiClient.patch<ApiResponse<PurchaseRequestItem>>(`/api/v1/procurement/requests/${requestId}/status`, { status });
    return res.data.data;
  },

  addCandidateSupplier: async (
    requestId: string,
    payload: { supplier_id: string; supplier_name: string; supplier_email?: string }
  ): Promise<CandidateSupplierItem> => {
    const res = await apiClient.post<ApiResponse<CandidateSupplierItem>>(
      `/api/v1/procurement/requests/${requestId}/candidate-suppliers`,
      payload
    );
    return res.data.data;
  },

  listQuotations: async (requestId: string): Promise<QuotationItem[]> => {
    const res = await apiClient.get<ApiResponse<QuotationItem[]>>(`/api/v1/procurement/requests/${requestId}/quotations`);
    return res.data.data;
  },

  submitQuotation: async (
    requestId: string,
    payload: {
      supplier_id: string;
      quotation_number: string;
      total_cost: number;
      currency: string;
      estimated_delivery_days: number;
      warranty_terms?: string;
      payment_terms?: string;
      document_id?: string;
    }
  ): Promise<QuotationItem> => {
    const res = await apiClient.post<ApiResponse<QuotationItem>>(`/api/v1/procurement/requests/${requestId}/quotations`, payload);
    return res.data.data;
  },

  recordDecision: async (
    requestId: string,
    payload: {
      action: 'APPROVE' | 'REJECT';
      decision_reason: string;
      selected_supplier_id?: string;
      selected_quotation_id?: string;
    }
  ): Promise<PurchaseRequestDetail> => {
    const res = await apiClient.post<ApiResponse<PurchaseRequestDetail>>(
      `/api/v1/procurement/requests/${requestId}/decision`,
      payload
    );
    return res.data.data;
  },
};

// ----------------- Document & Extraction API -----------------
export interface ExtractedLineItem {
  item_name: string;
  specification?: string;
  quantity: number;
  unit_of_measure: string;
  unit_price: number;
  total_price: number;
  confidence_score: number;
}

export interface StructuredQuotationData {
  supplier_name?: string;
  quotation_number?: string;
  document_date?: string;
  currency: string;
  subtotal?: number;
  tax_amount?: number;
  discount_amount?: number;
  total_cost?: number;
  delivery_lead_time_days?: number;
  payment_terms?: string;
  warranty_terms?: string;
  line_items: ExtractedLineItem[];
  overall_confidence: number;
  arithmetic_valid: boolean;
  flagged_reasons: string[];
}

export interface ExtractionResponse {
  id: string;
  document_id: string;
  organization_id: string;
  purchase_request_id?: string;
  supplier_id?: string;
  supplier_name?: string;
  quotation_number?: string;
  currency: string;
  total_cost?: number;
  overall_confidence: number;
  arithmetic_valid: boolean;
  is_verified: boolean;
  verified_by?: string;
  verified_at?: string;
  flagged_reasons: string[];
  structured_data: StructuredQuotationData;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  file_name: string;
  file_size: number;
  content_type: string;
  storage_path: string;
  status: string;
  checksum_sha256?: string;
  purchase_request_id?: string;
  supplier_id?: string;
  created_at: string;
}

export const documentApi = {
  upload: async (file: File, purchaseRequestId?: string, supplierId?: string): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append('file', file);
    if (purchaseRequestId) formData.append('purchase_request_id', purchaseRequestId);
    if (supplierId) formData.append('supplier_id', supplierId);

    const res = await apiClient.post<ApiResponse<DocumentItem>>('/api/v1/document/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data.data;
  },

  list: async (purchaseRequestId?: string): Promise<DocumentItem[]> => {
    const params = purchaseRequestId ? { purchase_request_id: purchaseRequestId } : {};
    const res = await apiClient.get<ApiResponse<DocumentItem[]>>('/api/v1/document/documents', { params });
    return res.data.data;
  },

  triggerExtract: async (documentId: string): Promise<ExtractionResponse> => {
    const res = await apiClient.post<ApiResponse<ExtractionResponse>>(`/api/v1/document/documents/${documentId}/extract`);
    return res.data.data;
  },

  getExtraction: async (documentId: string): Promise<ExtractionResponse> => {
    const res = await apiClient.get<ApiResponse<ExtractionResponse>>(`/api/v1/document/documents/${documentId}/extraction`);
    return res.data.data;
  },

  correctExtraction: async (documentId: string, payload: Partial<StructuredQuotationData>): Promise<ExtractionResponse> => {
    const res = await apiClient.put<ApiResponse<ExtractionResponse>>(`/api/v1/document/documents/${documentId}/extraction`, payload);
    return res.data.data;
  },

  verifyExtraction: async (documentId: string): Promise<ExtractionResponse> => {
    const res = await apiClient.post<ApiResponse<ExtractionResponse>>(`/api/v1/document/documents/${documentId}/verify`);
    return res.data.data;
  },
};

// ----------------- AI Orchestrator API -----------------
export interface WorkflowStatusResponse {
  workflow_id: string;
  correlation_id: string;
  organization_id: string;
  purchase_request_id: string;
  document_id?: string;
  supplier_id?: string;
  status: string;
  current_step: string;
  requires_human_review: boolean;
  human_review_reason?: string;
  state: Record<string, any>;
  created_at: string;
}

export const aiOrchestratorApi = {
  startWorkflow: async (payload: {
    purchase_request_id: string;
    document_id?: string;
    supplier_id?: string;
    extracted_data?: StructuredQuotationData;
    is_verified?: boolean;
  }): Promise<WorkflowStatusResponse> => {
    const res = await apiClient.post<ApiResponse<WorkflowStatusResponse>>('/api/v1/ai-orchestrator/workflows/start', payload);
    return res.data.data;
  },

  getWorkflowStatus: async (workflowId: string): Promise<WorkflowStatusResponse> => {
    const res = await apiClient.get<ApiResponse<WorkflowStatusResponse>>(`/api/v1/ai-orchestrator/workflows/${workflowId}/status`);
    return res.data.data;
  },

  resumeWorkflow: async (workflowId: string, payload: {
    updated_extracted_data?: StructuredQuotationData;
    confirm_human_verification?: boolean;
  }): Promise<WorkflowStatusResponse> => {
    const res = await apiClient.post<ApiResponse<WorkflowStatusResponse>>(`/api/v1/ai-orchestrator/workflows/${workflowId}/resume`, payload);
    return res.data.data;
  },
};

// ----------------- Risk Assessment API -----------------
export interface RiskEvaluationResponse {
  assessment_id: string;
  supplier_id: string;
  supplier_name: string;
  risk_score?: number | null;
  risk_category: string;
  confidence: number;
  data_sufficiency: string;
  observation_count: number;
  metrics_breakdown: Record<string, any>;
  explanation: string;
  model_version: string;
  created_at: string;
}

export const riskApi = {
  evaluate: async (payload: {
    supplier_id: string;
    supplier_name: string;
    delivery_records?: any[];
    quality_records?: any[];
  }): Promise<RiskEvaluationResponse> => {
    const res = await apiClient.post<RiskEvaluationResponse>('/api/v1/risk/evaluate', payload);
    return res.data;
  },

  getSupplierLatest: async (supplierId: string): Promise<RiskEvaluationResponse> => {
    const res = await apiClient.get<RiskEvaluationResponse>(`/api/v1/risk/suppliers/${supplierId}`);
    return res.data;
  },
};

// ----------------- Optimization API -----------------
export interface RankedSupplierItem {
  rank: number;
  supplier_id: string;
  supplier_name: string;
  quotation_id: string;
  total_cost: number;
  lead_time_days: number;
  is_eligible: boolean;
  rejection_reasons: string[];
  composite_score: number;
  normalized_scores: Record<string, number>;
  explanation: string;
}

export interface OptimizationResponse {
  scenario_id: string;
  request_id: string;
  algorithm: string;
  total_evaluated: number;
  eligible_count: number;
  rejected_count: number;
  top_recommended_supplier_id?: string;
  top_recommended_supplier_name?: string;
  rankings: RankedSupplierItem[];
  weights_used: Record<string, number>;
  decision_summary: string;
  created_at: string;
}

export const optimizationApi = {
  rank: async (payload: {
    request_id: string;
    budget_limit: number;
    currency?: string;
    candidates: any[];
    constraints?: any;
    weights?: any;
  }): Promise<OptimizationResponse> => {
    const res = await apiClient.post<OptimizationResponse>('/api/v1/optimization/rank', payload);
    return res.data;
  },

  getScenario: async (scenarioId: string): Promise<OptimizationResponse> => {
    const res = await apiClient.get<OptimizationResponse>(`/api/v1/optimization/scenarios/${scenarioId}`);
    return res.data;
  },

  getLatestForRequest: async (requestId: string): Promise<OptimizationResponse> => {
    const res = await apiClient.get<OptimizationResponse>(`/api/v1/optimization/requests/${requestId}`);
    return res.data;
  },
};

