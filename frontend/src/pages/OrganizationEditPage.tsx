import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import OrganizationForm from '../components/OrganizationForm';
import { useOrganizationQuery } from '../app/queries/organizationQueries';
import { organizationService } from '../services/organizationService';

const OrganizationEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const organizationId = id ?? '';
  const navigate = useNavigate();

  const organizationQuery = useOrganizationQuery(organizationId, {
    enabled: Boolean(organizationId),
  });

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (payload: any) => {
    if (!organizationId) return;

    try {
      setSubmitting(true);
      setSubmitError(null);
      await organizationService.updateOrganization(organizationId, payload);
      navigate(`/admin/organizations/${organizationId}`);
    } catch (error: any) {
      console.error('Error updating organization:', error);
      setSubmitError(error?.message || 'Failed to update organization');
    } finally {
      setSubmitting(false);
    }
  };

  if (organizationQuery.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (organizationQuery.error || !organizationQuery.data) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          {organizationQuery.error instanceof Error
            ? organizationQuery.error.message
            : 'Organization not found'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h4">Edit Organization</Typography>
          <Typography variant="body2" color="text.secondary">
            Update organizational details. Only modified fields will be saved.
          </Typography>
        </Stack>
        <OrganizationForm
          organization={organizationQuery.data}
          mode="edit"
          onSubmit={handleSubmit}
          onClose={() => navigate(`/admin/organizations/${organizationId}`)}
          loading={submitting}
          error={submitError}
        />
      </Paper>
    </Box>
  );
};

export default OrganizationEditPage;
