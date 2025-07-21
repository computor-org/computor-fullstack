import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Grid,
  IconButton,
  Stack,
  Divider,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { UserGet } from '../types/generated/users';
import { apiClient } from '../services/apiClient';

interface UserFormData {
  given_name: string;
  family_name: string;
  email: string;
  username: string;
  user_type: 'user' | 'token';
}

const UserEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [user, setUser] = useState<UserGet | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  
  const [formData, setFormData] = useState<UserFormData>({
    given_name: '',
    family_name: '',
    email: '',
    username: '',
    user_type: 'user',
  });

  useEffect(() => {
    loadUser();
  }, [id]);

  const loadUser = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);
      
      const userData = await apiClient.getUserById(id);
      setUser(userData);
      
      // Initialize form with user data
      setFormData({
        given_name: userData.given_name || '',
        family_name: userData.family_name || '',
        email: userData.email || '',
        username: userData.username || '',
        user_type: userData.user_type || 'user',
      });
    } catch (err: any) {
      console.error('Error loading user:', err);
      setError('Failed to load user details');
    } finally {
      setLoading(false);
    }
  };

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

  const handleSave = async () => {
    if (!validateForm() || !user) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // For updates, exclude user_type as it's not allowed in UserUpdate interface
      const { user_type, ...rawUpdateData } = formData;
      
      // Only send fields that have actually changed and are not empty
      const updateData: any = {};
      
      if (rawUpdateData.given_name && rawUpdateData.given_name.trim() !== user.given_name) {
        updateData.given_name = rawUpdateData.given_name.trim();
      }
      if (rawUpdateData.family_name && rawUpdateData.family_name.trim() !== user.family_name) {
        updateData.family_name = rawUpdateData.family_name.trim();
      }
      if (rawUpdateData.email && rawUpdateData.email.trim() !== user.email) {
        updateData.email = rawUpdateData.email.trim();
      }
      if (rawUpdateData.username && rawUpdateData.username.trim() !== user.username) {
        updateData.username = rawUpdateData.username.trim();
      }
      
      // Only send the update if there are actual changes
      if (Object.keys(updateData).length === 0) {
        console.log('No changes detected, returning to detail page');
        navigate(`/admin/users/${id}`);
        return;
      }
      
      await apiClient.updateUser(user.id, updateData);
      
      // Navigate back to detail page
      navigate(`/admin/users/${id}`);
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
        setError('Failed to update user. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    navigate(`/admin/users/${id}`);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !user) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin/users')} sx={{ mt: 2 }}>
          Back to Users
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate(`/admin/users/${id}`)}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Edit User</Typography>
      </Box>

      {/* Form */}
      <Paper sx={{ p: 3, maxWidth: 800 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            User Information
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Update the user's basic information below. Some fields may be restricted based on user type.
          </Typography>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="First Name"
              value={formData.given_name}
              onChange={(e) => handleInputChange('given_name', e.target.value)}
              error={!!fieldErrors.given_name}
              helperText={fieldErrors.given_name}
              disabled={saving}
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
              disabled={saving}
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
              disabled={saving}
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
              disabled={saving}
              required
            />
          </Grid>

          <Grid item xs={12} sm={4}>
            <FormControl fullWidth disabled={true}>
              <InputLabel>User Type</InputLabel>
              <Select
                value={formData.user_type}
                label="User Type"
              >
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="token">Token</MenuItem>
              </Select>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                User type cannot be changed after creation
              </Typography>
            </FormControl>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* Actions */}
        <Stack direction="row" spacing={2} justifyContent="flex-end">
          <Button
            onClick={handleCancel}
            disabled={saving}
            color="inherit"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
};

export default UserEditPage;