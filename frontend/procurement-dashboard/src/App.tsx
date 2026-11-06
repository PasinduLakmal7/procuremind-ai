import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './components/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { SuppliersPage } from './pages/SuppliersPage';
import { RequestsPage } from './pages/RequestsPage';
import { QuotationsPage } from './pages/QuotationsPage';
import { RiskOptimizationPage } from './pages/RiskOptimizationPage';
import { AuditCompliancePage } from './pages/AuditCompliancePage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/requests" element={<RequestsPage />} />
              <Route path="/suppliers" element={<SuppliersPage />} />
              <Route path="/quotations" element={<QuotationsPage />} />
              <Route path="/risk-optimization" element={<RiskOptimizationPage />} />
              <Route path="/audit-trail" element={<AuditCompliancePage />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
