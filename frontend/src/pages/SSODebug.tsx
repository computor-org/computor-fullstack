import React, { useEffect, useState } from 'react';
import { Box, Paper, Typography, Button, Alert, CircularProgress } from '@mui/material';
import { SSOAuthService } from '../services/ssoAuthService';
import { apiClient } from '../api/client';
import { useAuth } from '../hooks/useAuth';

const SSODebug: React.FC = () => {
  const { state: authState } = useAuth();
  const [loading, setLoading] = useState(false);
  const [apiResponse, setApiResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const testAPI = async () => {
    setLoading(true);
    setError(null);
    setApiResponse(null);

    try {
      const response = await apiClient.get('/auth/me');
      setApiResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'API call failed');
    } finally {
      setLoading(false);
    }
  };

  const getStoredData = () => {
    const authToken = localStorage.getItem('auth_token');
    const authUser = localStorage.getItem('auth_user');
    
    return {
      authToken: authToken ? JSON.parse(authToken) : null,
      authUser: authUser ? JSON.parse(authUser) : null,
      ssoAuth: SSOAuthService.getStoredAuth(),
    };
  };

  const [storedData, setStoredData] = useState(getStoredData());

  useEffect(() => {
    const interval = setInterval(() => {
      setStoredData(getStoredData());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>SSO Debug Page</Typography>
      
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Auth State (from hook)</Typography>
        <pre style={{ overflow: 'auto' }}>
          {JSON.stringify(authState, null, 2)}
        </pre>
      </Paper>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Stored Auth Data</Typography>
        <pre style={{ overflow: 'auto' }}>
          {JSON.stringify(storedData, null, 2)}
        </pre>
      </Paper>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Test API Call</Typography>
        <Button 
          variant="contained" 
          onClick={testAPI} 
          disabled={loading}
          sx={{ mb: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Test /auth/me Endpoint'}
        </Button>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {apiResponse && (
          <pre style={{ overflow: 'auto' }}>
            {JSON.stringify(apiResponse, null, 2)}
          </pre>
        )}
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Actions</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            variant="outlined" 
            onClick={() => SSOAuthService.initiateSSO()}
          >
            Login with Keycloak
          </Button>
          <Button 
            variant="outlined" 
            onClick={() => window.location.href = '/dashboard'}
          >
            Go to Dashboard
          </Button>
          <Button 
            variant="outlined" 
            color="error"
            onClick={() => {
              localStorage.clear();
              window.location.reload();
            }}
          >
            Clear Storage & Reload
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default SSODebug;