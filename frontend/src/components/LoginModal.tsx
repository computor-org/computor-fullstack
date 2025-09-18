import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  Typography,
  Chip,
  Stack,
  Divider,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../hooks/useAuth';
import { AuthService } from '../services/authService';
import { LoginCredentials } from '../types/auth';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

interface LoginModalProps {
  open: boolean;
  onClose: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ open, onClose }) => {
  const { login, state, clearError } = useAuth();
  const [showDemoCredentials, setShowDemoCredentials] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
    reset,
  } = useForm<LoginCredentials>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset();
      clearError();
    }
  }, [open, reset, clearError]);

  useEffect(() => {
    if (state.isAuthenticated) {
      onClose();
    }
  }, [state.isAuthenticated, onClose]);

  const onSubmit = async (data: LoginCredentials) => {
    await login(data);
  };

  const handleDemoLogin = (role: 'admin' | 'lecturer' | 'student') => {
    const credentials = AuthService.getDemoCredentials()[role];
    setValue('username', credentials.username);
    setValue('password', credentials.password);
  };

  const handleQuickLogin = async (role: 'admin' | 'lecturer' | 'student') => {
    const credentials = AuthService.getDemoCredentials()[role];
    await login(credentials);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
          Sign In
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Welcome to Computor Course Management
        </Typography>
        {state.error && (
          <Typography variant="caption" color="error" display="block" sx={{ mt: 1 }}>
            💡 If you can't type in fields, use the direct login buttons below
          </Typography>
        )}
      </DialogTitle>
      
      <DialogContent>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ mt: 1 }}>
          {state.error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {state.error}
            </Alert>
          )}

          <Controller
            name="username"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Username"
                type="text"
                fullWidth
                margin="normal"
                error={!!errors.username}
                helperText={errors.username?.message}
                disabled={state.isLoading}
                autoComplete="username"
                placeholder="Enter username or use demo buttons below"
              />
            )}
          />

          <Controller
            name="password"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Password"
                type="password"
                fullWidth
                margin="normal"
                error={!!errors.password}
                helperText={errors.password?.message}
                disabled={state.isLoading}
                autoComplete="current-password"
                placeholder="Enter password or use demo buttons below"
              />
            )}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={state.isLoading}
            sx={{ mt: 3, mb: 2 }}
          >
            {state.isLoading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              'Sign In'
            )}
          </Button>

          <Divider sx={{ my: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Demo Accounts - Choose Your Experience
            </Typography>
          </Divider>

          <Stack spacing={2}>
            <Typography variant="body2" color="text.secondary" align="center">
              <strong>Option 1:</strong> Click to auto-fill credentials, then click "Sign In"
            </Typography>
            
            <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap">
              <Chip
                label="📋 Fill Admin"
                onClick={() => handleDemoLogin('admin')}
                variant="outlined"
                color="error"
                size="small"
                disabled={state.isLoading}
              />
              <Chip
                label="📋 Fill Lecturer"
                onClick={() => handleDemoLogin('lecturer')}
                variant="outlined"
                color="primary"
                size="small"
                disabled={state.isLoading}
              />
              <Chip
                label="📋 Fill Student"
                onClick={() => handleDemoLogin('student')}
                variant="outlined"
                color="secondary"
                size="small"
                disabled={state.isLoading}
              />
            </Stack>

            <Typography variant="body2" color="text.secondary" align="center">
              <strong>Option 2:</strong> Click to login directly (recommended)
            </Typography>
            
            <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap">
              <Button
                variant="contained"
                color="error"
                size="small"
                onClick={() => handleQuickLogin('admin')}
                disabled={state.isLoading}
                sx={{ minWidth: 100 }}
              >
                🔑 Admin Login
              </Button>
              <Button
                variant="contained"
                color="primary"
                size="small"
                onClick={() => handleQuickLogin('lecturer')}
                disabled={state.isLoading}
                sx={{ minWidth: 100 }}
              >
                🔑 Lecturer Login
              </Button>
              <Button
                variant="contained"
                color="secondary"
                size="small"
                onClick={() => handleQuickLogin('student')}
                disabled={state.isLoading}
                sx={{ minWidth: 100 }}
              >
                🔑 Student Login
              </Button>
            </Stack>

            <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary" align="center" display="block">
                <strong>Demo Credentials:</strong><br/>
                Admin: admin@university.edu / admin123<br/>
                Lecturer: lecturer@university.edu / lecturer123<br/>
                Student: student@university.edu / student123
              </Typography>
            </Box>
          </Stack>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default LoginModal;
