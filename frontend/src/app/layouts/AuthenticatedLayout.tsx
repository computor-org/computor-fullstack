import React from 'react';
import { Box } from '@mui/material';
import Sidebar from '../../components/Sidebar';
import { useSidebar } from '../../hooks/useSidebar';
import { useAuth } from '../../hooks/useAuth';
import TopBar from '../components/TopBar';
import AppRoutes from '../routes/AppRoutes';

const AuthenticatedLayout: React.FC = () => {
  const { config, updateConfig, currentNavigation, contextInfo } = useSidebar();
  const { state: authState } = useAuth();

  if (!authState.isAuthenticated || !authState.user) {
    return null;
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <TopBar />

      <Sidebar
        navigation={currentNavigation}
        config={config}
        onConfigChange={updateConfig}
        contextInfo={contextInfo}
      />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 2,
          mt: 8,
          transition: 'margin 0.3s ease',
          overflow: 'auto',
        }}
      >
        <AppRoutes />
      </Box>
    </Box>
  );
};

export default AuthenticatedLayout;
