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
import { OrganizationGet, OrganizationCreate, OrganizationUpdate } from '../types/generated/organizations';
import { HierarchyTaskService } from '../services/hierarchyTaskService';
import { apiClient } from '../services/apiClient';

interface OrganizationTaskFormProps {
  organization?: OrganizationGet | null;
  mode: 'create' | 'edit';
  onSubmit?: (data: OrganizationCreate | OrganizationUpdate) => void;
  onTaskComplete?: (organizationId: string) => void;
  onClose?: () => void;
  renderActions?: boolean; // If false, actions will not be rendered (for external control)
  hideStatusAlerts?: boolean; // If true, status alerts will not be shown (parent will handle them)
}

export interface OrganizationTaskFormHandle {
  isProcessing: boolean;
  taskStatus: string | null;
  taskProgress: number;
  taskError: string | null;
  taskId: string | null;
  handleSubmit: (e?: React.FormEvent) => void;
}

const OrganizationTaskForm = React.forwardRef<OrganizationTaskFormHandle, OrganizationTaskFormProps>(({
  organization,
  mode,
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

  const [gitlabEnabled, setGitlabEnabled] = useState(false);
  const [gitlabConfig, setGitlabConfig] = useState({
    gitlab_url: '',
    gitlab_token: '',
    parent_group_id: '',
  });

  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [taskProgress, setTaskProgress] = useState(0);
  const [taskError, setTaskError] = useState<string | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

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

  // GitLab config fields are left empty for manual entry
  // The TEST_GITLAB_* variables are only for testing/deployment, not for system use

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleGitlabChange = (field: string, value: any) => {
    setGitlabConfig(prev => ({ ...prev, [field]: value }));
  };

  const monitorTask = async (taskId: string) => {
    setIsMonitoring(true);
    let attempts = 0;
    const maxAttempts = 120; // 2 minutes with 1-second intervals

    const checkStatus = async () => {
      try {
        const status = await HierarchyTaskService.getTaskStatus(taskId);
        
        if (status.status === 'COMPLETED') {
          setTaskStatus('completed');
          setTaskProgress(100);
          setIsMonitoring(false);
          
          // Extract organization ID from result
          if (status.result?.organization_id) {
            if (onTaskComplete) {
              onTaskComplete(status.result.organization_id);
            }
          }
          
          return true;
        } else if (status.status === 'FAILED') {
          setTaskStatus('failed');
          setTaskError(status.message || 'Task failed');
          setIsMonitoring(false);
          return true;
        } else if (status.status === 'RUNNING') {
          // Update progress if available
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

    // Initial check
    const completed = await checkStatus();
    if (!completed) {
      // Set up polling
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
    
    if (mode === 'create' && gitlabEnabled) {
      // Use task-based creation
      setTaskStatus('submitting');
      setTaskError(null);
      
      try {
        const organizationData = {
          ...formData,
          properties: {},
        };
        
        const response = await HierarchyTaskService.createOrganization({
          organization: organizationData,
          gitlab: {
            gitlab_url: gitlabConfig.gitlab_url,
            gitlab_token: gitlabConfig.gitlab_token,
          },
          parent_group_id: parseInt(gitlabConfig.parent_group_id, 10),
        });
        
        setTaskId(response.task_id);
        setTaskStatus('submitted');
        
        // Start monitoring the task
        await monitorTask(response.task_id);
      } catch (error: any) {
        setTaskStatus('error');
        setTaskError(error.message || 'Failed to submit task');
      }
    } else {
      // Use traditional synchronous approach
      if (mode === 'create') {
        const createData: OrganizationCreate = {
          ...formData,
          properties: {},
        };
        if (onSubmit) {
          onSubmit(createData);
        }
      } else {
        // For update, only send changed fields
        const updateData: OrganizationUpdate = {};
        Object.keys(formData).forEach((key) => {
          const value = (formData as any)[key];
          if (value && value !== (organization as any)?.[key]) {
            (updateData as any)[key] = value;
          }
        });
        if (onSubmit) {
          onSubmit(updateData);
        }
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
    handleSubmit,
  }), [isProcessing, taskStatus, taskProgress, taskError, taskId, handleSubmit]);

  return (
    <Box component="form" onSubmit={handleSubmit}>
      {mode === 'create' && (
        <Box sx={{ mb: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={gitlabEnabled}
                onChange={(e) => setGitlabEnabled(e.target.checked)}
                disabled={isProcessing}
              />
            }
            label="Create with GitLab integration"
          />
        </Box>
      )}

      {!hideStatusAlerts && taskStatus && taskStatus !== 'completed' && (
        <Box sx={{ mb: 2 }}>
          {taskStatus === 'submitting' && (
            <Alert severity="info">Submitting organization creation task...</Alert>
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
                Creating organization... {taskProgress}%
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
            <Alert severity="success">
              Organization created successfully!
            </Alert>
          )}
        </Box>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Title"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            required={formData.organization_type !== 'user'}
            disabled={formData.organization_type === 'user' || isProcessing}
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
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Path"
            value={formData.path}
            onChange={(e) => handleChange('path', e.target.value)}
            required
            helperText="Use underscores instead of hyphens (e.g., my_org not my-org)"
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth required disabled={isProcessing}>
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

        {gitlabEnabled && mode === 'create' && (
          <>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                GitLab Configuration
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="GitLab URL"
                value={gitlabConfig.gitlab_url}
                onChange={(e) => handleGitlabChange('gitlab_url', e.target.value)}
                required={gitlabEnabled}
                disabled={isProcessing}
                helperText="e.g., https://gitlab.com"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="GitLab Token"
                type="password"
                value={gitlabConfig.gitlab_token}
                onChange={(e) => handleGitlabChange('gitlab_token', e.target.value)}
                required={gitlabEnabled}
                disabled={isProcessing}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Parent Group ID"
                value={gitlabConfig.parent_group_id}
                onChange={(e) => handleGitlabChange('parent_group_id', e.target.value)}
                required={gitlabEnabled}
                disabled={isProcessing}
                helperText="GitLab parent group ID"
              />
            </Grid>
          </>
        )}

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Number/ID"
            value={formData.number}
            onChange={(e) => handleChange('number', e.target.value)}
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Telephone"
            value={formData.telephone}
            onChange={(e) => handleChange('telephone', e.target.value)}
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Website URL"
            value={formData.url}
            onChange={(e) => handleChange('url', e.target.value)}
            helperText="Must start with http:// or https://"
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Street Address"
            value={formData.street_address}
            onChange={(e) => handleChange('street_address', e.target.value)}
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="City/Locality"
            value={formData.locality}
            onChange={(e) => handleChange('locality', e.target.value)}
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <TextField
            fullWidth
            label="State/Region"
            value={formData.region}
            onChange={(e) => handleChange('region', e.target.value)}
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <TextField
            fullWidth
            label="Postal Code"
            value={formData.postal_code}
            onChange={(e) => handleChange('postal_code', e.target.value)}
            disabled={isProcessing}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Country"
            value={formData.country}
            onChange={(e) => handleChange('country', e.target.value)}
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
            disabled={isProcessing || taskStatus === 'completed'}
            startIcon={isProcessing ? <CircularProgress size={20} /> : null}
          >
            {isProcessing ? 'Processing...' : (mode === 'create' ? 'Create' : 'Update')}
          </Button>
        </DialogActions>
      )}
    </Box>
  );
});

OrganizationTaskForm.displayName = 'OrganizationTaskForm';

export default OrganizationTaskForm;