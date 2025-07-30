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
} from '@mui/material';
import { CourseGet, CourseCreate, CourseUpdate, CourseFamilyGet } from '../types/generated/courses';
import { HierarchyTaskService, TaskStatusMapper } from '../services/hierarchyTaskService';
import { apiClient } from '../services/apiClient';

interface CourseTaskFormProps {
  course?: CourseGet | null;
  mode: 'create' | 'edit';
  courseFamilyId?: string;
  onSubmit?: (data: CourseCreate | CourseUpdate) => void;
  onTaskComplete?: (courseId: string) => void;
  onClose?: () => void;
  renderActions?: boolean;
  hideStatusAlerts?: boolean;
}

export interface CourseTaskFormHandle {
  isProcessing: boolean;
  taskStatus: string | null;
  taskProgress: number;
  taskError: string | null;
  taskId: string | null;
  createdEntityId: string | null;
  createdEntityName: string | null;
  handleSubmit: (e?: React.FormEvent) => void;
}

const CourseTaskForm = React.forwardRef<CourseTaskFormHandle, CourseTaskFormProps>(({
  course,
  mode,
  courseFamilyId,
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

  const [courseFamilies, setCourseFamilies] = useState<CourseFamilyGet[]>([]);
  const [selectedFamilyId, setSelectedFamilyId] = useState<string>(courseFamilyId || '');
  const [loadingFamilies, setLoadingFamilies] = useState(true);

  const [hasParentGitlab, setHasParentGitlab] = useState(false);
  const [organizationName, setOrganizationName] = useState<string>('');

  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [taskProgress, setTaskProgress] = useState(0);
  const [taskError, setTaskError] = useState<string | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [createdEntityId, setCreatedEntityId] = useState<string | null>(null);
  const [createdEntityName, setCreatedEntityName] = useState<string | null>(null);

  // Load course families for dropdown
  useEffect(() => {
    const loadCourseFamilies = async () => {
      try {
        setLoadingFamilies(true);
        const families = await apiClient.get<CourseFamilyGet[]>('/course-families');
        setCourseFamilies(families);
      } catch (error) {
        console.error('Failed to load course families:', error);
      } finally {
        setLoadingFamilies(false);
      }
    };

    if (mode === 'create') {
      loadCourseFamilies();
    }
  }, [mode]);

  useEffect(() => {
    if (course && mode === 'edit') {
      setFormData({
        title: course.title || '',
        description: course.description || '',
        path: course.path,
        properties: course.properties || {},
      });
      setSelectedFamilyId(course.course_family_id);
    }
  }, [course, mode]);

  // Check if selected course family has GitLab integration
  useEffect(() => {
    if (selectedFamilyId && courseFamilies.length > 0) {
      const family = courseFamilies.find(f => f.id === selectedFamilyId);
      setHasParentGitlab(!!family?.properties?.gitlab?.group_id);
      
      // Get organization name for display
      if (family?.organization) {
        setOrganizationName(family.organization.title || 'the organization');
      }
    }
  }, [selectedFamilyId, courseFamilies]);

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
            if (resultResponse.result?.result?.course_id) {
              setCreatedEntityId(resultResponse.result.result.course_id);
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
      // Always use task-based creation for courses
      setTaskStatus('submitting');
      setTaskError(null);
      
      try {
        const courseData = {
          ...formData,
          course_family_id: selectedFamilyId,
        };
        
        const response = await HierarchyTaskService.createCourse({
          course: courseData,
          course_family_id: selectedFamilyId,
          // No GitLab config needed - backend will use course family's config
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
      const updateData: CourseUpdate = {};
      Object.keys(formData).forEach((key) => {
        const value = (formData as any)[key];
        if (value && value !== (course as any)?.[key]) {
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
      {mode === 'create' && selectedFamilyId && (
        <Box sx={{ mb: 2 }}>
          {hasParentGitlab ? (
            <Alert severity="info">
              A GitLab subgroup will be created under the course family's GitLab group.
              GitLab credentials will be inherited from {organizationName}.
            </Alert>
          ) : (
            <Alert severity="info">
              The course will be created without GitLab integration as the parent course family doesn't have GitLab configured.
            </Alert>
          )}
        </Box>
      )}

      {!hideStatusAlerts && taskStatus && taskStatus !== 'completed' && (
        <Box sx={{ mb: 2 }}>
          {taskStatus === 'submitting' && (
            <Alert severity="info">Submitting course creation task...</Alert>
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
                Creating course... {taskProgress}%
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
                    onClick={() => window.open(`/admin/courses/${createdEntityId}`, '_blank')}
                    sx={{ ml: 1 }}
                  >
                    View Course
                  </Button>
                )
              }
            >
              Course "{createdEntityName || 'Unnamed'}" created successfully!
            </Alert>
          )}
        </Box>
      )}

      <Grid container spacing={2}>
        {mode === 'create' && !courseFamilyId && (
          <Grid item xs={12}>
            <FormControl fullWidth required disabled={loadingFamilies || isProcessing}>
              <InputLabel>Course Family</InputLabel>
              <Select
                value={selectedFamilyId}
                onChange={(e) => setSelectedFamilyId(e.target.value)}
                label="Course Family"
              >
                {courseFamilies.map((family) => (
                  <MenuItem key={family.id} value={family.id}>
                    {family.title || `Course Family ${family.id}`}
                    {family.organization && ` - ${family.organization.title}`}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>Select the parent course family for this course</FormHelperText>
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
            helperText="Display name for the course"
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
            helperText="Use underscores instead of hyphens (e.g., my_course not my-course)"
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
            disabled={isProcessing || taskStatus === 'completed' || (mode === 'create' && !selectedFamilyId)}
            startIcon={isProcessing ? <CircularProgress size={20} /> : null}
          >
            {isProcessing ? 'Processing...' : (mode === 'create' ? 'Create' : 'Update')}
          </Button>
        </DialogActions>
      )}
    </Box>
  );
});

CourseTaskForm.displayName = 'CourseTaskForm';

export default CourseTaskForm;