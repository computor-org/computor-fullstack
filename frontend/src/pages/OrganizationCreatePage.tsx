import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  Typography,
  Stack,
} from '@mui/material';
import { OrganizationCreate, OrganizationUpdate } from '../types/generated/organizations';
import { apiClient } from '../services/apiClient';
import OrganizationTaskForm, { OrganizationTaskFormHandle } from '../components/OrganizationTaskForm';
import { FormPageLayout } from '../components/common/FormPageLayout';

const OrganizationCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const formRef = useRef<OrganizationTaskFormHandle>(null);

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
    // No longer automatically redirecting - success UI shows navigation button instead
    console.log(`Organization created with ID: ${organizationId}`);
  };

  const handleCancel = () => {
    navigate('/admin/organizations');
  };

  const handleSubmit = () => {
    formRef.current?.handleSubmit();
  };

  const [formState, setFormState] = useState({
    isProcessing: false,
    taskStatus: null as string | null,
    taskProgress: 0,
    taskError: null as string | null,
    taskId: null as string | null,
    createdEntityId: null as string | null,
    createdEntityName: null as string | null,
  });

  // Update form state when ref changes
  useEffect(() => {
    const interval = setInterval(() => {
      if (formRef.current) {
        setFormState({
          isProcessing: formRef.current.isProcessing,
          taskStatus: formRef.current.taskStatus,
          taskProgress: formRef.current.taskProgress,
          taskError: formRef.current.taskError,
          taskId: formRef.current.taskId,
          createdEntityId: formRef.current.createdEntityId,
          createdEntityName: formRef.current.createdEntityName,
        });
      }
    }, 100);
    return () => clearInterval(interval);
  }, []);

  // Header content with alerts and progress indicators
  const headerContent = (
    <Stack spacing={2}>
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {formState.taskStatus && formState.taskStatus !== 'completed' && (
        <>
          {formState.taskStatus === 'submitting' && (
            <Alert severity="info">Submitting organization creation task...</Alert>
          )}
          {formState.taskStatus === 'submitted' && (
            <Alert severity="info">
              Task submitted successfully. Task ID: {formState.taskId}
              <LinearProgress sx={{ mt: 1 }} />
            </Alert>
          )}
          {formState.isProcessing && formState.taskProgress > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                Creating organization... {formState.taskProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={formState.taskProgress} sx={{ mt: 1 }} />
            </Box>
          )}
          {formState.taskStatus === 'failed' && (
            <Alert severity="error">
              Task failed: {formState.taskError || 'Unknown error'}
            </Alert>
          )}
          {formState.taskStatus === 'timeout' && (
            <Alert severity="warning">
              Task monitoring timed out. Task ID: {formState.taskId}
            </Alert>
          )}
          {formState.taskStatus === 'completed' && (
            <Alert 
              severity="success" 
              action={
                formState.createdEntityId && (
                  <Button 
                    color="inherit" 
                    size="small"
                    variant="outlined"
                    onClick={() => window.open(`/admin/organizations/${formState.createdEntityId}`, '_blank')}
                    sx={{ ml: 1 }}
                  >
                    View Organization
                  </Button>
                )
              }
            >
              Organization "{formState.createdEntityName || 'Unnamed'}" created successfully!
            </Alert>
          )}
        </>
      )}
    </Stack>
  );

  // Action buttons for the fixed footer
  const actions = (
    <>
      <Button
        onClick={handleCancel}
        disabled={formState.isProcessing}
        color="inherit"
        sx={{ mr: 2 }}
      >
        Cancel
      </Button>
      <Button
        onClick={handleSubmit}
        variant="contained"
        disabled={formState.isProcessing || formState.taskStatus === 'completed' || loading}
        startIcon={formState.isProcessing ? <CircularProgress size={20} /> : null}
      >
        {formState.isProcessing ? 'Processing...' : 'Create Organization'}
      </Button>
    </>
  );

  return (
    <FormPageLayout
      title="Create Organization"
      subtitle="Create a new organization. You can optionally enable GitLab integration to automatically create a GitLab group."
      onBack={handleCancel}
      headerContent={headerContent}
      actions={actions}
    >
      <OrganizationTaskForm
        ref={formRef}
        mode="create"
        onSubmit={handleFormSubmit}
        onTaskComplete={handleTaskComplete}
        renderActions={false}
        hideStatusAlerts={true}
      />
    </FormPageLayout>
  );
};

export default OrganizationCreatePage;