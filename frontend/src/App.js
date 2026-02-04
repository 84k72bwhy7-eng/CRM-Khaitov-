import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';
import './App.css';

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ClientsPage from './pages/ClientsPage';
import ClientDetailPage from './pages/ClientDetailPage';
import PaymentsPage from './pages/PaymentsPage';
import UsersPage from './pages/UsersPage';
import SettingsPage from './pages/SettingsPage';
import ActivityLogPage from './pages/ActivityLogPage';

// Layout
import Layout from './components/Layout';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

const AdminRoute = ({ children }) => {
  const { isAdmin } = useAuth();
  
  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

function AppRoutes() {
  const { user } = useAuth();
  
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout>
            <DashboardPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/clients" element={
        <ProtectedRoute>
          <Layout>
            <ClientsPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/clients/:id" element={
        <ProtectedRoute>
          <Layout>
            <ClientDetailPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/payments" element={
        <ProtectedRoute>
          <Layout>
            <PaymentsPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/users" element={
        <ProtectedRoute>
          <AdminRoute>
            <Layout>
              <UsersPage />
            </Layout>
          </AdminRoute>
        </ProtectedRoute>
      } />
      <Route path="/activity-log" element={
        <ProtectedRoute>
          <AdminRoute>
            <Layout>
              <ActivityLogPage />
            </Layout>
          </AdminRoute>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <Layout>
            <SettingsPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <Toaster position="top-right" richColors />
          <AppRoutes />
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}

export default App;
