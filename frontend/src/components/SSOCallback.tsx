import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import { SSOIntegration } from '../services/ssoIntegration';

const SSOCallback: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('Processing authentication...');

  useEffect(() => {
    const processCallback = async () => {
      try {
        // Parse URL parameters
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');
        const refreshToken = params.get('refresh_token');
        const userId = params.get('user_id');
        
        console.log('SSOCallback: Processing with token:', token?.substring(0, 20) + '...');

        if (!token) {
          throw new Error('No authentication token received');
        }

        // Store tokens in localStorage
        const authToken = {
          accessToken: token,
          refreshToken: refreshToken || '',
          expiresAt: Date.now() + (24 * 60 * 60 * 1000), // 24 hours
        };
        
        localStorage.setItem('auth_token', JSON.stringify(authToken));
        
        // Fetch user data from API using SSOIntegration
        setStatus('Fetching user information...');
        const syncSuccess = await SSOIntegration.syncAuthData();
        
        if (!syncSuccess) {
          throw new Error('Failed to fetch user information');
        }
        
        // Clear the URL parameters
        window.history.replaceState({}, document.title, '/auth/success');
        
        // Get redirect path or default to dashboard
        const redirectPath = sessionStorage.getItem('auth_redirect') || '/dashboard';
        sessionStorage.removeItem('auth_redirect');
        
        setStatus('Authentication successful! Redirecting...');
        console.log('SSOCallback: Authentication successful, redirecting to:', redirectPath);
        
        // Small delay to show success message
        setTimeout(() => {
          // Use navigate for client-side routing
          navigate(redirectPath);
        }, 500);
        
      } catch (err) {
        console.error('SSOCallback error:', err);
        setError(err instanceof Error ? err.message : 'Authentication failed');
        
        // Redirect to login after showing error
        setTimeout(() => {
          navigate('/');
        }, 3000);
      }
    };

    // Process immediately
    processCallback();
  }, [navigate]);

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      bgcolor="background.default"
    >
      {error ? (
        <Alert severity="error" sx={{ mb: 2, maxWidth: 400 }}>
          {error}
        </Alert>
      ) : (
        <>
          <CircularProgress size={60} sx={{ mb: 2 }} />
          <Typography variant="h6">{status}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Please wait while we complete your authentication...
          </Typography>
        </>
      )}
    </Box>
  );
};

export default SSOCallback;