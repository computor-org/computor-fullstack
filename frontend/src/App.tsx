import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { SidebarProvider } from './hooks/useSidebar';
import { AuthProvider, useAuth } from './hooks/useAuth';
import AuthenticatedLayout from './app/layouts/AuthenticatedLayout';
import UnauthenticatedLayout from './app/layouts/UnauthenticatedLayout';
import SSOCallback from './components/SSOCallback';
import QueryProvider from './app/providers/QueryProvider';

const AppContent: React.FC = () => {
  const { state: authState } = useAuth();
  const isSSoCallback =
    window.location.pathname === '/auth/success' ||
    window.location.pathname === '/auth/callback';

  if (isSSoCallback) {
    return <SSOCallback />;
  }

  if (authState.isLoading || !authState.isAuthenticated || !authState.user) {
    return <UnauthenticatedLayout />;
  }

  return (
    <SidebarProvider user={authState.user}>
      <AuthenticatedLayout />
    </SidebarProvider>
  );
};

function App() {
  return (
    <Router>
      <QueryProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </QueryProvider>
    </Router>
  );
}

export default App;
