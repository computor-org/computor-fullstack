import React from 'react';
import {
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { ExampleRepository } from '../types/examples';

const repositorySchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  source_type: z.enum(['git', 'minio', 'github', 's3', 'gitlab'], {
    required_error: 'Source type is required',
  }),
  source_url: z.string().min(1, 'Source URL is required'),
  access_credentials: z.string().optional(),
  default_version: z.string().optional(),
  organization_id: z.string().optional(),
});

type RepositoryFormData = z.infer<typeof repositorySchema>;

interface ExampleRepositoryFormProps {
  repository: ExampleRepository | null;
  onSave: (data: Omit<ExampleRepository, 'id' | 'created_at' | 'updated_at'>) => void;
  onCancel: () => void;
}

const ExampleRepositoryForm: React.FC<ExampleRepositoryFormProps> = ({
  repository,
  onSave,
  onCancel,
}) => {
  const {
    control,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RepositoryFormData>({
    resolver: zodResolver(repositorySchema),
    defaultValues: {
      name: repository?.name || '',
      description: repository?.description || '',
      source_type: repository?.source_type || 'minio',
      source_url: repository?.source_url || '',
      access_credentials: repository?.access_credentials || '',
      default_version: repository?.default_version || '',
      organization_id: repository?.organization_id || '',
    },
  });

  const watchedSourceType = watch('source_type');

  const getSourceTypeHelperText = (sourceType: string) => {
    switch (sourceType) {
      case 'git':
        return 'Git repository URL (e.g., https://github.com/user/repo.git)';
      case 'github':
        return 'GitHub repository URL (e.g., https://github.com/user/repo)';
      case 'gitlab':
        return 'GitLab repository URL (e.g., https://gitlab.com/user/repo.git)';
      case 'minio':
        return 'MinIO bucket path (e.g., examples-bucket/folder)';
      case 's3':
        return 'S3 bucket path (e.g., my-bucket/examples)';
      default:
        return 'Repository source URL';
    }
  };

  const getCredentialsHelperText = (sourceType: string) => {
    switch (sourceType) {
      case 'git':
      case 'github':
      case 'gitlab':
        return 'Access token or credentials for private repositories';
      case 'minio':
      case 's3':
        return 'JSON credentials: {"access_key": "...", "secret_key": "..."}';
      default:
        return 'Access credentials if required';
    }
  };

  const getDefaultVersionHelperText = (sourceType: string) => {
    switch (sourceType) {
      case 'git':
      case 'github':
      case 'gitlab':
        return 'Git branch name (e.g., main, master)';
      case 'minio':
      case 's3':
        return 'Default version tag (optional)';
      default:
        return 'Default version or branch';
    }
  };

  const onSubmit = (data: RepositoryFormData) => {
    onSave(data as Omit<ExampleRepository, 'id' | 'created_at' | 'updated_at'>);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <DialogTitle>
        {repository ? 'Edit Repository' : 'Add New Repository'}
      </DialogTitle>
      
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          {/* Repository Name */}
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Repository Name"
                fullWidth
                error={!!errors.name}
                helperText={errors.name?.message}
                placeholder="Python Basics Examples"
              />
            )}
          />

          {/* Description */}
          <Controller
            name="description"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Description"
                fullWidth
                multiline
                rows={2}
                placeholder="Collection of basic Python programming examples"
              />
            )}
          />

          {/* Source Type */}
          <Controller
            name="source_type"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.source_type}>
                <InputLabel>Source Type</InputLabel>
                <Select {...field} label="Source Type">
                  <MenuItem value="minio">MinIO</MenuItem>
                  <MenuItem value="git">Git</MenuItem>
                  <MenuItem value="github">GitHub</MenuItem>
                  <MenuItem value="gitlab">GitLab</MenuItem>
                  <MenuItem value="s3">Amazon S3</MenuItem>
                </Select>
                {errors.source_type && (
                  <Typography variant="caption" color="error">
                    {errors.source_type.message}
                  </Typography>
                )}
              </FormControl>
            )}
          />

          {/* Source URL */}
          <Controller
            name="source_url"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Source URL"
                fullWidth
                error={!!errors.source_url}
                helperText={errors.source_url?.message || getSourceTypeHelperText(watchedSourceType)}
                placeholder={
                  watchedSourceType === 'minio' 
                    ? 'examples-bucket/python-basics'
                    : 'https://github.com/user/repo.git'
                }
              />
            )}
          />

          {/* Access Credentials */}
          <Controller
            name="access_credentials"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Access Credentials"
                fullWidth
                multiline={watchedSourceType === 'minio' || watchedSourceType === 's3'}
                rows={watchedSourceType === 'minio' || watchedSourceType === 's3' ? 3 : 1}
                type={watchedSourceType === 'minio' || watchedSourceType === 's3' ? 'text' : 'password'}
                helperText={getCredentialsHelperText(watchedSourceType)}
                placeholder={
                  watchedSourceType === 'minio' || watchedSourceType === 's3'
                    ? '{"access_key": "your_key", "secret_key": "your_secret"}'
                    : 'your_access_token'
                }
              />
            )}
          />

          {/* Default Version */}
          <Controller
            name="default_version"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Default Version"
                fullWidth
                helperText={getDefaultVersionHelperText(watchedSourceType)}
                placeholder={
                  watchedSourceType === 'git' || watchedSourceType === 'github' || watchedSourceType === 'gitlab'
                    ? 'main'
                    : 'v1.0'
                }
              />
            )}
          />

          {/* Security Warning */}
          {watchedSourceType !== 'minio' && (
            <Alert severity="info">
              <Typography variant="body2">
                For Git-based repositories, the system will sync examples to MinIO storage 
                for versioned management and fast access.
              </Typography>
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onCancel}>
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </form>
  );
};

export default ExampleRepositoryForm;