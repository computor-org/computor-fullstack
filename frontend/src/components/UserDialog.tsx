import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Grid,
  Typography,
  Box,
} from '@mui/material';
import { User } from '../types';
import { apiClient } from '../services/apiClient';

interface UserDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  user?: User | null; // If provided, we're editing; if null/undefined, we're creating
  mode: 'create' | 'edit';
}

interface UserFormData {
  given_name: string;
  family_name: string;
  email: string;
  username: string;
  user_type: 'user' | 'token';
}

const UserDialog: React.FC<UserDialogProps> = ({
  open,
  onClose,
  onSuccess,
  user,
  mode
}) => {
  const [formData, setFormData] = useState<UserFormData>({
    given_name: '',
    family_name: '',
    email: '',
    username: '',
    user_type: 'user',
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Initialize form data when user prop changes
  useEffect(() => {
    if (mode === 'edit' && user) {
      setFormData({
        given_name: user.given_name || '',
        family_name: user.family_name || '',
        email: user.email || '',
        username: user.username || '',
        user_type: user.user_type || 'user',
      });
    } else if (mode === 'create') {
      setFormData({
        given_name: '',
        family_name: '',
        email: '',
        username: '',
        user_type: 'user',
      });
    }
    setError(null);
    setFieldErrors({});
  }, [user, mode, open]);

  const handleInputChange = (field: keyof UserFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear field error when user starts typing
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Required field validation
    if (!formData.given_name.trim()) {
      errors.given_name = 'First name is required';
    }
    if (!formData.family_name.trim()) {
      errors.family_name = 'Last name is required';
    }
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters long';
    } else if (!/^[a-zA-Z0-9._-]+$/.test(formData.username)) {
      errors.username = 'Username can only contain letters, numbers, dots, hyphens, and underscores';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (mode === 'create') {
        await apiClient.createUser(formData);
      } else if (mode === 'edit' && user) {
        await apiClient.updateUser(user.id, formData);
      }
      
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Error saving user:', err);
      
      // Handle specific API errors
      if (err.message.includes('409') || err.message.includes('conflict')) {
        if (err.message.toLowerCase().includes('email')) {
          setFieldErrors({ email: 'A user with this email already exists' });
        } else if (err.message.toLowerCase().includes('username')) {
          setFieldErrors({ username: 'A user with this username already exists' });
        } else {
          setError('A user with these details already exists');
        }
      } else if (err.message.includes('400')) {
        setError('Invalid user data. Please check your input and try again.');
      } else if (err.message.includes('403')) {
        setError('You do not have permission to perform this action');
      } else {
        setError(`Failed to ${mode} user. Please try again.`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { minHeight: 400 }
      }}
    >
      <DialogTitle>
        <Typography variant="h6">
          {mode === 'create' ? 'Create New User' : `Edit User: ${user?.given_name} ${user?.family_name}`}
        </Typography>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 1 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="First Name"
                value={formData.given_name}
                onChange={(e) => handleInputChange('given_name', e.target.value)}
                error={!!fieldErrors.given_name}
                helperText={fieldErrors.given_name}
                disabled={loading}
                required
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={formData.family_name}
                onChange={(e) => handleInputChange('family_name', e.target.value)}
                error={!!fieldErrors.family_name}
                helperText={fieldErrors.family_name}
                disabled={loading}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                error={!!fieldErrors.email}
                helperText={fieldErrors.email}
                disabled={loading}
                required
              />
            </Grid>

            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                label="Username"
                value={formData.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
                error={!!fieldErrors.username}
                helperText={fieldErrors.username || 'Username can contain letters, numbers, dots, hyphens, and underscores'}
                disabled={loading}
                required
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <FormControl fullWidth disabled={loading}>
                <InputLabel>User Type</InputLabel>
                <Select
                  value={formData.user_type}
                  label="User Type"
                  onChange={(e) => handleInputChange('user_type', e.target.value as 'user' | 'token')}
                >
                  <MenuItem value="user">User</MenuItem>
                  <MenuItem value="token">Token</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, pt: 1 }}>
        <Button
          onClick={handleClose}
          disabled={loading}
          color="inherit"
        >
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : undefined}
        >
          {loading ? 'Saving...' : mode === 'create' ? 'Create User' : 'Update User'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UserDialog;