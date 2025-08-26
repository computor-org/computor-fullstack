import React, { useState, useEffect } from 'react';
import {
  Chip,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
} from '@mui/icons-material';
import { apiClient } from '../services/apiClient';

interface DeploymentStatusChipProps {
  courseId: string;
  deploymentTaskId?: string | null;
  deploymentStatus?: string | null;
  exampleVersion?: string | null;
}

interface DeploymentStatusResponse {
  status: 'running' | 'completed' | 'failed';
  progress?: {
    completed: number;
    total: number;
    current: string;
  };
  results?: Array<{
    course_content_id: string;
    example_id: string;
    status: string;
    target_path: string;
  }>;
}

const DeploymentStatusChip: React.FC<DeploymentStatusChipProps> = ({
  courseId,
  deploymentTaskId,
  deploymentStatus,
  exampleVersion,
}) => {
  const [status, setStatus] = useState(deploymentStatus);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    // Poll for status if deploying
    if (deploymentTaskId && deploymentStatus === 'deploying') {
      const interval = setInterval(async () => {
        try {
          setChecking(true);
          const response = await apiClient.get<DeploymentStatusResponse>(
            `/api/v1/courses/${courseId}/deployment-status/${deploymentTaskId}`
          );
          
          if (response.status === 'completed') {
            setStatus('deployed');
            clearInterval(interval);
          } else if (response.status === 'failed') {
            setStatus('failed');
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Error checking deployment status:', err);
        } finally {
          setChecking(false);
        }
      }, 5000); // Check every 5 seconds

      return () => clearInterval(interval);
    }
  }, [courseId, deploymentTaskId, deploymentStatus]);

  const getChipProps = () => {
    switch (status) {
      case 'deploying':
        return {
          label: 'Deploying...',
          color: 'warning' as const,
          icon: checking ? <CircularProgress size={16} /> : <PendingIcon />,
        };
      case 'deployed':
      case 'released':
        return {
          label: `Example: ${exampleVersion || 'deployed'}`,
          color: 'success' as const,
          icon: <CheckIcon />,
        };
      case 'failed':
        return {
          label: 'Deployment failed',
          color: 'error' as const,
          icon: <ErrorIcon />,
        };
      case 'pending':
      case 'pending_release':
        return {
          label: 'Pending release',
          color: 'default' as const,
          icon: <PendingIcon />,
        };
      default:
        return {
          label: `Example: ${exampleVersion || 'deployed'}`,
          color: 'success' as const,
          icon: <CloudUploadIcon />,
        };
    }
  };

  const chipProps = getChipProps();

  return (
    <Tooltip title={`Deployment status: ${status}`}>
      <Chip
        {...chipProps}
        size="small"
        variant="outlined"
        sx={{ mr: 1 }}
      />
    </Tooltip>
  );
};

export default DeploymentStatusChip;