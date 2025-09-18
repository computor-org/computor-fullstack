import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import TopBar from '../components/TopBar';
import { useAuth } from '../../hooks/useAuth';

const UnauthenticatedLayout: React.FC = () => {
  const { state: authState } = useAuth();

  if (authState.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress size={40} />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <TopBar />
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: 'calc(100vh - 64px)',
          p: 3,
          textAlign: 'center',
        }}
      >
        <Typography variant="h4" gutterBottom>
          Welcome to Computor
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          University Programming Course Management Platform
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Please sign in to access your courses and materials.
        </Typography>
      </Box>
    </Box>
  );
};

export default UnauthenticatedLayout;
