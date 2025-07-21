import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Alert,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { OrganizationCreate, OrganizationUpdate } from '../types/generated/organizations';
import { apiClient } from '../services/apiClient';
import OrganizationTaskForm from '../components/OrganizationTaskForm';

const OrganizationCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFormSubmit = async (data: OrganizationCreate | OrganizationUpdate) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.post('/organizations', data);
      // Navigate to organizations list after successful creation
      navigate('/admin/organizations');
    } catch (err: any) {
      console.error('Error creating organization:', err);
      setError(err.message || 'Failed to create organization');
    } finally {
      setLoading(false);
    }
  };

  const handleTaskComplete = (organizationId: string) => {
    // Navigate to the newly created organization's detail page
    navigate(`/admin/organizations/${organizationId}`);
  };

  const handleCancel = () => {
    navigate('/admin/organizations');
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={handleCancel}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Create Organization</Typography>
      </Box>

      {/* Main Content */}
      <Paper sx={{ p: 3, maxWidth: 1000 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            New Organization
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create a new organization. You can optionally enable GitLab integration to automatically 
            create a GitLab group for this organization.
          </Typography>
        </Box>

        <OrganizationTaskForm
          mode="create"
          onSubmit={handleFormSubmit}
          onTaskComplete={handleTaskComplete}
          onClose={handleCancel}
        />
      </Paper>
    </Box>
  );
};

export default OrganizationCreatePage;