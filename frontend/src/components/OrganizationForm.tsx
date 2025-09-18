import React, { useState, useEffect } from 'react';
import {
  Alert,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Box,
  FormHelperText,
  DialogActions,
  Button,
} from '@mui/material';
import { OrganizationGet, OrganizationCreate, OrganizationUpdate } from '../types/generated/organizations';

interface OrganizationFormProps {
  organization?: OrganizationGet | null;
  mode: 'create' | 'edit';
  onSubmit: (data: OrganizationCreate | OrganizationUpdate) => Promise<void> | void;
  onClose?: () => void;
  loading?: boolean;
  error?: string | null;
}

const OrganizationForm: React.FC<OrganizationFormProps> = ({
  organization,
  mode,
  onSubmit,
  onClose,
  loading = false,
  error = null,
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    path: '',
    organization_type: 'organization' as 'user' | 'community' | 'organization',
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
    if (organization && mode === 'edit') {
      setFormData({
        title: organization.title || '',
        description: organization.description || '',
        path: organization.path,
        organization_type: organization.organization_type as any,
        number: organization.number || '',
        email: organization.email || '',
        telephone: organization.telephone || '',
        url: organization.url || '',
        street_address: organization.street_address || '',
        locality: organization.locality || '',
        region: organization.region || '',
        postal_code: organization.postal_code || '',
        country: organization.country || '',
      });
    }
  }, [organization, mode]);

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (mode === 'create') {
      const createData: OrganizationCreate = {
        ...formData,
        properties: {},
      };
      await onSubmit(createData);
    } else {
      // For update, only send changed fields
      const updateData: OrganizationUpdate = {};
      Object.keys(formData).forEach((key) => {
        const value = (formData as any)[key];
        if (value && value !== (organization as any)?.[key]) {
          (updateData as any)[key] = value;
        }
      });
      if (Object.keys(updateData).length > 0) {
        await onSubmit(updateData);
      } else {
        onClose?.();
      }
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Title"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            required={formData.organization_type !== 'user'}
            disabled={formData.organization_type === 'user'}
            helperText={formData.organization_type === 'user' ? 'User organizations cannot have a title' : ''}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            multiline
            rows={3}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Path"
            value={formData.path}
            onChange={(e) => handleChange('path', e.target.value)}
            required
            helperText="Hierarchical path (e.g., org.department.team)"
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth required>
            <InputLabel>Organization Type</InputLabel>
            <Select
              value={formData.organization_type}
              onChange={(e) => handleChange('organization_type', e.target.value)}
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
            onChange={(e) => handleChange('number', e.target.value)}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Telephone"
            value={formData.telephone}
            onChange={(e) => handleChange('telephone', e.target.value)}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Website URL"
            value={formData.url}
            onChange={(e) => handleChange('url', e.target.value)}
            helperText="Must start with http:// or https://"
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Street Address"
            value={formData.street_address}
            onChange={(e) => handleChange('street_address', e.target.value)}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="City/Locality"
            value={formData.locality}
            onChange={(e) => handleChange('locality', e.target.value)}
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <TextField
            fullWidth
            label="State/Region"
            value={formData.region}
            onChange={(e) => handleChange('region', e.target.value)}
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <TextField
            fullWidth
            label="Postal Code"
            value={formData.postal_code}
            onChange={(e) => handleChange('postal_code', e.target.value)}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Country"
            value={formData.country}
            onChange={(e) => handleChange('country', e.target.value)}
          />
        </Grid>
      </Grid>
      <DialogActions>
        {onClose && (
          <Button onClick={onClose} color="inherit" disabled={loading}>
            Cancel
          </Button>
        )}
        <Button type="submit" variant="contained" color="primary" disabled={loading}>
          {loading ? 'Saving...' : mode === 'create' ? 'Create' : 'Update'}
        </Button>
      </DialogActions>
    </Box>
  );
};

export default OrganizationForm;
