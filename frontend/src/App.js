import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Loader2 } from 'lucide-react';

import Login from './pages/Login';
import Chat from './pages/Chat';
import JobWorkspace from './pages/JobWorkspace';
import Settings from './pages/Settings';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center"><Loader2 className="w-7 h-7 animate-spin text-purple-400" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppShell() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
      <Route path="/jobs/:jobId" element={<ProtectedRoute><JobWorkspace /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppShell />
        <Toaster
          theme="dark"
          position="top-right"
          toastOptions={{
            style: {
              background: 'rgba(15, 17, 25, 0.85)',
              border: '1px solid rgba(124, 58, 237, 0.25)',
              backdropFilter: 'blur(20px)',
              color: '#f8fafc',
            },
          }}
        />
      </BrowserRouter>
    </AuthProvider>
  );
}
