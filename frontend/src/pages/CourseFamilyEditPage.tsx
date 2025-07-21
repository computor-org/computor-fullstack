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
import { CourseFamilyGet, CourseFamilyUpdate } from '../types/generated/courses';
import { OrganizationGet } from '../types/generated/organizations';
import { apiClient } from '../services/apiClient';

interface CourseFamilyFormData {
  title: string;
  description: string;
  path: string;
  organization_id: string;
}

const CourseFamilyEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [courseFamily, setCourseFamily] = useState<CourseFamilyGet | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationGet[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  
  const [formData, setFormData] = useState<CourseFamilyFormData>({
    title: '',
    description: '',
    path: '',
    organization_id: '',
  });

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);
      
      // Load course family and organizations in parallel
      const [cfData, orgsResponse] = await Promise.all([
        apiClient.get<CourseFamilyGet>(`/course-families/${id}`),
        apiClient.get<any>('/organizations', { params: { limit: 100 } })
      ]);

      setCourseFamily(cfData);
      
      const orgsData = Array.isArray(orgsResponse) ? orgsResponse : orgsResponse.data || [];
      setOrganizations(orgsData);
      
      // Initialize form with course family data
      setFormData({
        title: cfData.title || '',
        description: cfData.description || '',
        path: cfData.path || '',
        organization_id: cfData.organization_id || '',
      });
    } catch (err: any) {
      console.error('Error loading data:', err);
      setError('Failed to load course family details');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof CourseFamilyFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear field error when user starts typing
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Required field validation
    if (!formData.title.trim()) {
      errors.title = 'Title is required';
    }
    
    if (!formData.path.trim()) {
      errors.path = 'Path is required';
    }

    if (!formData.organization_id) {
      errors.organization_id = 'Organization is required';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm() || !courseFamily) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Only send fields that have actually changed and are not empty
      const updateData: any = {};
      
      Object.keys(formData).forEach((key) => {
        const value = (formData as any)[key];
        if (value && value !== (courseFamily as any)?.[key]) {
          updateData[key] = value;
        }
      });
      
      // Only send the update if there are actual changes
      if (Object.keys(updateData).length === 0) {
        console.log('No changes detected, returning to detail page');
        navigate(`/admin/course-families/${id}`);
        return;
      }
      
      await apiClient.patch(`/course-families/${courseFamily.id}`, updateData);
      
      // Navigate back to detail page
      navigate(`/admin/course-families/${id}`);
    } catch (err: any) {
      console.error('Error saving course family:', err);
      
      // Handle specific API errors
      if (err.message.includes('409') || err.message.includes('conflict')) {
        setError('A course family with these details already exists');
      } else if (err.message.includes('400')) {
        setError('Invalid course family data. Please check your input and try again.');
      } else if (err.message.includes('403')) {
        setError('You do not have permission to perform this action');
      } else {
        setError('Failed to update course family. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    navigate(`/admin/course-families/${id}`);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !courseFamily) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin/course-families')} sx={{ mt: 2 }}>
          Back to Course Families
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate(`/admin/course-families/${id}`)}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Edit Course Family</Typography>
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
            Course Family Information
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Update the course family's details below.
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
              helperText={fieldErrors.title || 'Course family display name'}
              disabled={saving}
              required
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
              helperText="Brief description of the course family"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Path"
              value={formData.path}
              onChange={(e) => handleInputChange('path', e.target.value)}
              error={!!fieldErrors.path}
              helperText={fieldErrors.path || 'Hierarchical path within organization'}
              disabled={saving}
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth required disabled={saving} error={!!fieldErrors.organization_id}>
              <InputLabel>Organization</InputLabel>
              <Select
                value={formData.organization_id}
                onChange={(e) => handleInputChange('organization_id', e.target.value)}
                label="Organization"
              >
                {organizations.map((org) => (
                  <MenuItem key={org.id} value={org.id}>
                    {org.title || `User Organization (${org.user_id?.substring(0, 8)}...)`}
                  </MenuItem>
                ))}
              </Select>
              {fieldErrors.organization_id && (
                <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.5 }}>
                  {fieldErrors.organization_id}
                </Typography>
              )}
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

export default CourseFamilyEditPage;