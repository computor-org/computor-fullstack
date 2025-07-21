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
import { OrganizationGet, OrganizationUpdate } from '../types/generated/organizations';
import { apiClient } from '../services/apiClient';

interface OrganizationFormData {
  title: string;
  description: string;
  path: string;
  organization_type: 'user' | 'community' | 'organization';
  number: string;
  email: string;
  telephone: string;
  url: string;
  street_address: string;
  locality: string;
  region: string;
  postal_code: string;
  country: string;
}

const OrganizationEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [organization, setOrganization] = useState<OrganizationGet | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  
  const [formData, setFormData] = useState<OrganizationFormData>({
    title: '',
    description: '',
    path: '',
    organization_type: 'organization',
    number: '',
    email: '',
    telephone: '',
    url: '',
    street_address: '',
    locality: '',
    region: '',
    postal_code: '',
    country: '',
  });

  useEffect(() => {
    loadOrganization();
  }, [id]);

  const loadOrganization = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);
      
      const orgData = await apiClient.get<OrganizationGet>(`/organizations/${id}`);
      setOrganization(orgData);
      
      // Initialize form with organization data
      setFormData({
        title: orgData.title || '',
        description: orgData.description || '',
        path: orgData.path || '',
        organization_type: orgData.organization_type as any || 'organization',
        number: orgData.number || '',
        email: orgData.email || '',
        telephone: orgData.telephone || '',
        url: orgData.url || '',
        street_address: orgData.street_address || '',
        locality: orgData.locality || '',
        region: orgData.region || '',
        postal_code: orgData.postal_code || '',
        country: orgData.country || '',
      });
    } catch (err: any) {
      console.error('Error loading organization:', err);
      setError('Failed to load organization details');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof OrganizationFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear field error when user starts typing
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Required field validation
    if (!formData.path.trim()) {
      errors.path = 'Path is required';
    }
    
    if (formData.organization_type !== 'user' && !formData.title.trim()) {
      errors.title = 'Title is required for non-user organizations';
    }

    // Email validation
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    // URL validation
    if (formData.url && !formData.url.startsWith('http://') && !formData.url.startsWith('https://')) {
      errors.url = 'URL must start with http:// or https://';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm() || !organization) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Only send fields that have actually changed and are not empty
      const updateData: any = {};
      
      Object.keys(formData).forEach((key) => {
        const value = (formData as any)[key];
        if (value && value !== (organization as any)?.[key]) {
          updateData[key] = value;
        }
      });
      
      // Only send the update if there are actual changes
      if (Object.keys(updateData).length === 0) {
        console.log('No changes detected, returning to detail page');
        navigate(`/admin/organizations/${id}`);
        return;
      }
      
      await apiClient.patch(`/organizations/${organization.id}`, updateData);
      
      // Navigate back to detail page
      navigate(`/admin/organizations/${id}`);
    } catch (err: any) {
      console.error('Error saving organization:', err);
      
      // Handle specific API errors
      if (err.message.includes('409') || err.message.includes('conflict')) {
        setError('An organization with these details already exists');
      } else if (err.message.includes('400')) {
        setError('Invalid organization data. Please check your input and try again.');
      } else if (err.message.includes('403')) {
        setError('You do not have permission to perform this action');
      } else {
        setError('Failed to update organization. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    navigate(`/admin/organizations/${id}`);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !organization) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin/organizations')} sx={{ mt: 2 }}>
          Back to Organizations
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate(`/admin/organizations/${id}`)}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Edit Organization</Typography>
      </Box>

      {/* Form */}
      <Paper sx={{ p: 3, maxWidth: 1000 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Organization Information
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Update the organization's details below.
          </Typography>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Title"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              error={!!fieldErrors.title}
              helperText={fieldErrors.title || 'Organization display name'}
              disabled={saving || formData.organization_type === 'user'}
              required={formData.organization_type !== 'user'}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              multiline
              rows={3}
              disabled={saving}
              helperText="Brief description of the organization"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Path"
              value={formData.path}
              onChange={(e) => handleInputChange('path', e.target.value)}
              error={!!fieldErrors.path}
              helperText={fieldErrors.path || 'Hierarchical path (e.g., org.department.team)'}
              disabled={saving}
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth required disabled={saving}>
              <InputLabel>Organization Type</InputLabel>
              <Select
                value={formData.organization_type}
                onChange={(e) => handleInputChange('organization_type', e.target.value)}
                label="Organization Type"
              >
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="community">Community</MenuItem>
                <MenuItem value="organization">Organization</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Number/ID"
              value={formData.number}
              onChange={(e) => handleInputChange('number', e.target.value)}
              disabled={saving}
              helperText="Optional organization identifier"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              error={!!fieldErrors.email}
              helperText={fieldErrors.email}
              disabled={saving}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Telephone"
              value={formData.telephone}
              onChange={(e) => handleInputChange('telephone', e.target.value)}
              disabled={saving}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Website URL"
              value={formData.url}
              onChange={(e) => handleInputChange('url', e.target.value)}
              error={!!fieldErrors.url}
              helperText={fieldErrors.url || 'Must start with http:// or https://'}
              disabled={saving}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Address Information
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Street Address"
              value={formData.street_address}
              onChange={(e) => handleInputChange('street_address', e.target.value)}
              disabled={saving}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="City/Locality"
              value={formData.locality}
              onChange={(e) => handleInputChange('locality', e.target.value)}
              disabled={saving}
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="State/Region"
              value={formData.region}
              onChange={(e) => handleInputChange('region', e.target.value)}
              disabled={saving}
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Postal Code"
              value={formData.postal_code}
              onChange={(e) => handleInputChange('postal_code', e.target.value)}
              disabled={saving}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Country"
              value={formData.country}
              onChange={(e) => handleInputChange('country', e.target.value)}
              disabled={saving}
            />
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

export default OrganizationEditPage;