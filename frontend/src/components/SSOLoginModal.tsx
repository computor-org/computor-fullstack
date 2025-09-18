import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Divider,
  Stack,
} from '@mui/material';
import { LoginOutlined, Key } from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { SSOAuthService } from '../services/ssoAuthService';

interface SSOLoginModalProps {
  open: boolean;
  onClose: () => void;
}

interface SSOProvider {
  name: string;
  display_name: string;
}

const SSOLoginModal: React.FC<SSOLoginModalProps> = ({ open, onClose }) => {
  const { state: authState, login, clearError } = useAuth();
  const [providers, setProviders] = useState<SSOProvider[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(true);

  // Basic auth form state (fallback)
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    if (open) {
      // Fetch SSO providers when modal opens
      SSOAuthService.getProviders()
        .then(setProviders)
        .catch(console.error)
        .finally(() => setLoadingProviders(false));
    }
  }, [open]);

  const handleSSOLogin = (provider: string) => {
    // Initiate SSO login
    SSOAuthService.initiateSSO(provider);
  };

  const handleBasicLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await login({ username, password });
    if (result.success) {
      onClose();
      setUsername('');
      setPassword('');
    }
  };

  const handleClose = () => {
    clearError();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center">
          <LoginOutlined sx={{ mr: 1 }} />
          Login to Computor
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {authState.error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {authState.error}
            </Alert>
          )}

          {/* SSO Login Options */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Single Sign-On
            </Typography>
            
            {loadingProviders ? (
              <Box display="flex" justifyContent="center" p={2}>
                <CircularProgress size={24} />
              </Box>
            ) : providers.length > 0 ? (
              <Stack spacing={1}>
                {providers.map((provider) => (
                  <Button
                    key={provider.name}
                    variant="contained"
                    fullWidth
                    startIcon={<Key />}
                    onClick={() => handleSSOLogin(provider.name)}
                    disabled={authState.isLoading}
                  >
                    Login with {provider.display_name}
                  </Button>
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No SSO providers available
              </Typography>
            )}
          </Box>

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" color="text.secondary">
              OR
            </Typography>
          </Divider>

          {/* Basic Auth Form (Fallback) */}
          <Box component="form" onSubmit={handleBasicLogin}>
            <Typography variant="subtitle2" gutterBottom>
              Login with Username
            </Typography>
            
            <TextField
              autoFocus
              margin="dense"
              label="Username"
              type="text"
              fullWidth
              variant="outlined"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={authState.isLoading}
              sx={{ mb: 2 }}
            />
            
            <TextField
              margin="dense"
              label="Password"
              type="password"
              fullWidth
              variant="outlined"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={authState.isLoading}
              sx={{ mb: 2 }}
            />

            <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
              <Button
                onClick={handleClose}
                disabled={authState.isLoading}
                fullWidth
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={authState.isLoading || !username || !password}
                fullWidth
              >
                {authState.isLoading ? (
                  <CircularProgress size={24} />
                ) : (
                  'Login'
                )}
              </Button>
            </Box>
          </Box>

        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default SSOLoginModal;
