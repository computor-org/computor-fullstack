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
import { CourseFamilyGet, CourseFamilyCreate, CourseFamilyUpdate } from '../types/generated/courses';
import { OrganizationGet } from '../types/generated/organizations';

interface CourseFamilyFormProps {
  courseFamily?: CourseFamilyGet | null;
  organizations: OrganizationGet[];
  mode: 'create' | 'edit';
  onSubmit: (data: CourseFamilyCreate | CourseFamilyUpdate) => Promise<void> | void;
  onClose?: () => void;
  loading?: boolean;
  error?: string | null;
}

const CourseFamilyForm: React.FC<CourseFamilyFormProps> = ({
  courseFamily,
  organizations,
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
    organization_id: '',
  });

  useEffect(() => {
    if (courseFamily && mode === 'edit') {
      setFormData({
        title: courseFamily.title || '',
        description: courseFamily.description || '',
        path: courseFamily.path,
        organization_id: courseFamily.organization_id,
      });
    }
  }, [courseFamily, mode]);

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (mode === 'create') {
      const createData: CourseFamilyCreate = {
        ...formData,
        properties: {},
      };
      await onSubmit(createData);
    } else {
      // For update, only send changed fields
      const updateData: CourseFamilyUpdate = {};
      Object.keys(formData).forEach((key) => {
        const value = (formData as any)[key];
        if (value !== (courseFamily as any)?.[key]) {
          (updateData as any)[key] = value || null;
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
            helperText="Name of the course family"
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
            helperText="Brief description of the course family"
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Path"
            value={formData.path}
            onChange={(e) => handleChange('path', e.target.value)}
            required
            helperText="Hierarchical path (e.g., cs.programming.intro)"
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth required>
            <InputLabel>Organization</InputLabel>
            <Select
              value={formData.organization_id}
              onChange={(e) => handleChange('organization_id', e.target.value)}
              label="Organization"
            >
              <MenuItem value="">
                <em>Select an organization</em>
              </MenuItem>
              {organizations.map((org) => (
                <MenuItem key={org.id} value={org.id}>
                  {org.title || `User Organization (${org.user_id?.substring(0, 8)}...)`}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>Organization that owns this course family</FormHelperText>
          </FormControl>
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

export default CourseFamilyForm;
