import React, { useState, useEffect } from 'react';
import {
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
  Alert,
  CircularProgress,
  Typography,
  LinearProgress,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { CourseFamilyGet, CourseFamilyCreate, CourseFamilyUpdate } from '../types/generated/courses';
import { OrganizationGet } from '../types/generated/organizations';
import { HierarchyTaskService, TaskStatusMapper } from '../services/hierarchyTaskService';
import { apiClient } from '../services/apiClient';

interface CourseFamilyTaskFormProps {
  courseFamily?: CourseFamilyGet | null;
  mode: 'create' | 'edit';
  organizationId?: string;
  onSubmit?: (data: CourseFamilyCreate | CourseFamilyUpdate) => void;
  onTaskComplete?: (courseFamilyId: string) => void;
  onClose?: () => void;
  renderActions?: boolean;
  hideStatusAlerts?: boolean;
}

export interface CourseFamilyTaskFormHandle {
  isProcessing: boolean;
  taskStatus: string | null;
  taskProgress: number;
  taskError: string | null;
  taskId: string | null;
  createdEntityId: string | null;
  createdEntityName: string | null;
  handleSubmit: (e?: React.FormEvent) => void;
}

const CourseFamilyTaskForm = React.forwardRef<CourseFamilyTaskFormHandle, CourseFamilyTaskFormProps>(({
  courseFamily,
  mode,
  organizationId,
  onSubmit,
  onTaskComplete,
  onClose,
  renderActions = true,
  hideStatusAlerts = false,
}, ref) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    path: '',
    properties: {},
  });

  const [organizations, setOrganizations] = useState<OrganizationGet[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>(organizationId || '');
  const [loadingOrgs, setLoadingOrgs] = useState(true);

  const [hasParentGitlab, setHasParentGitlab] = useState(false);

  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [taskProgress, setTaskProgress] = useState(0);
  const [taskError, setTaskError] = useState<string | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [createdEntityId, setCreatedEntityId] = useState<string | null>(null);
  const [createdEntityName, setCreatedEntityName] = useState<string | null>(null);

  // Load organizations for dropdown
  useEffect(() => {
    const loadOrganizations = async () => {
      try {
        setLoadingOrgs(true);
        const orgs = await apiClient.get<OrganizationGet[]>('/organizations');
        setOrganizations(orgs);
      } catch (error) {
        console.error('Failed to load organizations:', error);
      } finally {
        setLoadingOrgs(false);
      }
    };

    if (mode === 'create') {
      loadOrganizations();
    }
  }, [mode]);

  useEffect(() => {
    if (courseFamily && mode === 'edit') {
      setFormData({
        title: courseFamily.title || '',
        description: courseFamily.description || '',
        path: courseFamily.path,
        properties: courseFamily.properties || {},
      });
      setSelectedOrgId(courseFamily.organization_id);
    }
  }, [courseFamily, mode]);

  // Check if selected organization has GitLab integration
  useEffect(() => {
    if (selectedOrgId && organizations.length > 0) {
      const org = organizations.find(o => o.id === selectedOrgId);
      setHasParentGitlab(!!org?.properties?.gitlab?.group_id);
    }
  }, [selectedOrgId, organizations]);

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const monitorTask = async (taskId: string) => {
    setIsMonitoring(true);
    let attempts = 0;
    const maxAttempts = 120;

    const checkStatus = async () => {
      try {
        const status = await HierarchyTaskService.getTaskStatus(taskId);
        
        if (TaskStatusMapper.isSuccess(status.status)) {
          setTaskStatus('completed');
          setTaskProgress(100);
          setIsMonitoring(false);
          
          // Fetch the full result when task completes
          try {
            const resultResponse = await HierarchyTaskService.getTaskResult(taskId);
            if (resultResponse.result?.result?.course_family_id) {
              setCreatedEntityId(resultResponse.result.result.course_family_id);
              setCreatedEntityName(resultResponse.result.result?.name || formData.title);
            }
          } catch (error) {
            console.error('Error fetching task result:', error);
            // Fallback to formData title if result fetch fails
            setCreatedEntityName(formData.title);
          }
          
          return true;
        } else if (TaskStatusMapper.isFailed(status.status)) {
          setTaskStatus('failed');
          setTaskError(status.message || 'Task failed');
          setIsMonitoring(false);
          return true;
        } else if (TaskStatusMapper.isRunning(status.status)) {
          if (status.message) {
            const progressMatch = status.message.match(/progress: (\d+)/);
            if (progressMatch) {
              setTaskProgress(parseInt(progressMatch[1], 10));
            }
          }
        }
        
        return false;
      } catch (error) {
        console.error('Error checking task status:', error);
        attempts++;
        if (attempts >= maxAttempts) {
          setTaskStatus('timeout');
          setTaskError('Task monitoring timed out');
          setIsMonitoring(false);
          return true;
        }
        return false;
      }
    };

    const completed = await checkStatus();
    if (!completed) {
      const interval = setInterval(async () => {
        const done = await checkStatus();
        if (done) {
          clearInterval(interval);
        }
      }, 1000);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    
    if (mode === 'create') {
      // Always use task-based creation for course families
      setTaskStatus('submitting');
      setTaskError(null);
      
      try {
        const courseFamilyData = {
          ...formData,
          organization_id: selectedOrgId,
        };
        
        const response = await HierarchyTaskService.createCourseFamily({
          course_family: courseFamilyData,
          organization_id: selectedOrgId,
          // No GitLab config needed - backend will use org's config
        });
        
        setTaskId(response.task_id);
        setTaskStatus('submitted');
        
        await monitorTask(response.task_id);
      } catch (error: any) {
        setTaskStatus('error');
        setTaskError(error.message || 'Failed to submit task');
      }
    } else {
      // For update mode, use traditional synchronous approach
      const updateData: CourseFamilyUpdate = {};
      Object.keys(formData).forEach((key) => {
        const value = (formData as any)[key];
        if (value && value !== (courseFamily as any)?.[key]) {
          (updateData as any)[key] = value;
        }
      });
      if (onSubmit) {
        onSubmit(updateData);
      }
    }
  };

  const isProcessing = taskStatus === 'submitting' || taskStatus === 'submitted' || isMonitoring;

  // Expose form state and submit handler to parent
  React.useImperativeHandle(ref, () => ({
    isProcessing,
    taskStatus,
    taskProgress,
    taskError,
    taskId,
    createdEntityId,
    createdEntityName,
    handleSubmit,
  }), [isProcessing, taskStatus, taskProgress, taskError, taskId, createdEntityId, createdEntityName, handleSubmit]);

  return (
    <Box component="form" onSubmit={handleSubmit}>
      {mode === 'create' && selectedOrgId && (
        <Box sx={{ mb: 2 }}>
          {hasParentGitlab ? (
            <Alert severity="info">
              A GitLab subgroup will be created under the parent organization's GitLab group.
            </Alert>
          ) : (
            <Alert severity="info">
              The course family will be created without GitLab integration as the parent organization doesn't have GitLab configured.
            </Alert>
          )}
        </Box>
      )}

      {!hideStatusAlerts && taskStatus && taskStatus !== 'completed' && (
        <Box sx={{ mb: 2 }}>
          {taskStatus === 'submitting' && (
            <Alert severity="info">Submitting course family creation task...</Alert>
          )}
          {taskStatus === 'submitted' && (
            <Alert severity="info">
              Task submitted successfully. Task ID: {taskId}
              <LinearProgress sx={{ mt: 1 }} />
            </Alert>
          )}
          {isMonitoring && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                Creating course family... {taskProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={taskProgress} sx={{ mt: 1 }} />
            </Box>
          )}
          {taskStatus === 'failed' && (
            <Alert severity="error">
              Task failed: {taskError || 'Unknown error'}
            </Alert>
          )}
          {taskStatus === 'timeout' && (
            <Alert severity="warning">
              Task monitoring timed out. Task ID: {taskId}
            </Alert>
          )}
          {taskStatus === 'completed' && (
            <Alert 
              severity="success" 
              action={
                createdEntityId && (
                  <Button 
                    color="inherit" 
                    size="small"
                    variant="outlined"
                    onClick={() => window.open(`/admin/course-families/${createdEntityId}`, '_blank')}
                    sx={{ ml: 1 }}
                  >
                    View Course Family
                  </Button>
                )
              }
            >
              Course Family "{createdEntityName || 'Unnamed'}" created successfully!
            </Alert>
          )}
        </Box>
      )}

      <Grid container spacing={2}>
        {mode === 'create' && !organizationId && (
          <Grid item xs={12}>
            <FormControl fullWidth required disabled={loadingOrgs || isProcessing}>
              <InputLabel>Organization</InputLabel>
              <Select
                value={selectedOrgId}
                onChange={(e) => setSelectedOrgId(e.target.value)}
                label="Organization"
              >
                {organizations.map((org) => (
                  <MenuItem key={org.id} value={org.id}>
                    {org.title || `Organization ${org.id}`}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>Select the parent organization for this course family</FormHelperText>
            </FormControl>
          </Grid>
        )}

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Title"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            required
            disabled={isProcessing}
            helperText="Display name for the course family"
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
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Path"
            value={formData.path}
            onChange={(e) => handleChange('path', e.target.value)}
            required
            helperText="Use underscores instead of hyphens (e.g., my_course_family not my-course-family)"
            disabled={isProcessing}
          />
        </Grid>

      </Grid>
      
      {renderActions && (
        <DialogActions>
          {onClose && (
            <Button onClick={onClose} color="inherit" disabled={isProcessing}>
              Cancel
            </Button>
          )}
          <Button 
            type="submit" 
            variant="contained" 
            color="primary"
            disabled={isProcessing || taskStatus === 'completed' || (mode === 'create' && !selectedOrgId)}
            startIcon={isProcessing ? <CircularProgress size={20} /> : null}
          >
            {isProcessing ? 'Processing...' : (mode === 'create' ? 'Create' : 'Update')}
          </Button>
        </DialogActions>
      )}
    </Box>
  );
});

CourseFamilyTaskForm.displayName = 'CourseFamilyTaskForm';

export default CourseFamilyTaskForm;