import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  Typography,
  Stack,
} from '@mui/material';
import { CourseFamilyCreate, CourseFamilyUpdate } from '../types/generated/courses';
import { apiClient } from '../services/apiClient';
import CourseFamilyTaskForm, { CourseFamilyTaskFormHandle } from '../components/CourseFamilyTaskForm';
import { FormPageLayout } from '../components/common/FormPageLayout';

const CourseFamilyCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { organizationId } = useParams<{ organizationId?: string }>();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const formRef = useRef<CourseFamilyTaskFormHandle>(null);

  const handleFormSubmit = async (data: CourseFamilyCreate | CourseFamilyUpdate) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.post('/course-families', data);
      // Navigate to course families list after successful creation
      navigate('/admin/course-families');
    } catch (err: any) {
      console.error('Error creating course family:', err);
      setError(err.message || 'Failed to create course family');
    } finally {
      setLoading(false);
    }
  };

  const handleTaskComplete = () => {
    // Navigate to the course families list after successful creation
    navigate('/admin/course-families');
  };

  const handleCancel = () => {
    navigate('/admin/course-families');
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
        const newState = {
          isProcessing: formRef.current.isProcessing,
          taskStatus: formRef.current.taskStatus,
          taskProgress: formRef.current.taskProgress,
          taskError: formRef.current.taskError,
          taskId: formRef.current.taskId,
          createdEntityId: formRef.current.createdEntityId,
          createdEntityName: formRef.current.createdEntityName,
        };
        
        // Check if task just completed successfully
        if (newState.taskStatus === 'completed' && 
            formState.taskStatus !== 'completed') {
          handleTaskComplete();
        }
        
        setFormState(newState);
      }
    }, 100);
    return () => clearInterval(interval);
  }, [formState.taskStatus]);

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
            <Alert severity="info">Submitting course family creation task...</Alert>
          )}
          {formState.taskStatus === 'submitted' && (
            <Alert severity="info">
              Task submitted successfully. Task ID: {formState.taskId}
              <LinearProgress sx={{ mt: 1 }} />
            </Alert>
          )}
          {formState.isProcessing && formState.taskProgress > 0 && formState.taskStatus !== 'failed' && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                Creating course family... {formState.taskProgress}%
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
            <Alert severity="success">
              Course Family "{formState.createdEntityName || 'Unnamed'}" created successfully! Redirecting...
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
        startIcon={formState.isProcessing && formState.taskStatus !== 'failed' ? <CircularProgress size={20} /> : null}
      >
        {formState.isProcessing ? 'Processing...' : 'Create Course Family'}
      </Button>
    </>
  );

  return (
    <FormPageLayout
      title="Create Course Family"
      subtitle="Create a new course family within an organization. You can optionally enable GitLab integration to automatically create a GitLab subgroup."
      onBack={handleCancel}
      headerContent={headerContent}
      actions={actions}
    >
      <CourseFamilyTaskForm
        ref={formRef}
        mode="create"
        organizationId={organizationId}
        onSubmit={handleFormSubmit}
        onTaskComplete={handleTaskComplete}
        renderActions={false}
        hideStatusAlerts={true}
      />
    </FormPageLayout>
  );
};

export default CourseFamilyCreatePage;