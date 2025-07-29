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
  Chip,
  Box,
  Typography,
  IconButton,
} from '@mui/material';
import { Add as AddIcon, Close as CloseIcon } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Example, ExampleRepository } from '../types/examples';

const exampleSchema = z.object({
  example_repository_id: z.string().min(1, 'Repository is required'),
  directory: z.string()
    .min(1, 'Directory is required')
    .regex(/^[a-zA-Z0-9._-]+$/, 'Directory must contain only letters, numbers, dots, underscores, and hyphens'),
  identifier: z.string().min(1, 'Identifier is required'),
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  subject: z.string().optional(),
  category: z.string().optional(),
  tags: z.array(z.string()).default([]),
  version_identifier: z.string().optional(),
});

type ExampleFormData = z.infer<typeof exampleSchema>;

interface ExampleFormProps {
  example: Example | null;
  repositories: ExampleRepository[];
  onSave: (data: Omit<Example, 'id' | 'created_at' | 'updated_at'>) => void;
  onCancel: () => void;
}

const ExampleForm: React.FC<ExampleFormProps> = ({
  example,
  repositories,
  onSave,
  onCancel,
}) => {
  const [newTag, setNewTag] = React.useState('');

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ExampleFormData>({
    resolver: zodResolver(exampleSchema),
    defaultValues: {
      example_repository_id: example?.example_repository_id || '',
      directory: example?.directory || '',
      identifier: example?.identifier || '',
      title: example?.title || '',
      description: example?.description || '',
      subject: example?.subject || '',
      category: example?.category || '',
      tags: example?.tags || [],
      version_identifier: example?.version_identifier || '',
    },
  });

  const watchedTags = watch('tags');

  const handleAddTag = () => {
    if (newTag.trim() && !watchedTags.includes(newTag.trim())) {
      setValue('tags', [...watchedTags, newTag.trim()]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setValue('tags', watchedTags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleAddTag();
    }
  };

  const onSubmit = (data: ExampleFormData) => {
    onSave(data as Omit<Example, 'id' | 'created_at' | 'updated_at'>);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <DialogTitle>
        {example ? 'Edit Example' : 'Add New Example'}
      </DialogTitle>
      
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          {/* Repository Selection */}
          <Controller
            name="example_repository_id"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.example_repository_id}>
                <InputLabel>Repository</InputLabel>
                <Select {...field} label="Repository">
                  {repositories.map((repo) => (
                    <MenuItem key={repo.id} value={repo.id}>
                      <Box>
                        <Typography variant="body1">{repo.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {repo.source_type.toUpperCase()} • {repo.source_url}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
                {errors.example_repository_id && (
                  <Typography variant="caption" color="error">
                    {errors.example_repository_id.message}
                  </Typography>
                )}
              </FormControl>
            )}
          />

          {/* Directory */}
          <Controller
            name="directory"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Directory"
                fullWidth
                error={!!errors.directory}
                helperText={errors.directory?.message || 'Directory name in the repository (e.g., hello-world)'}
                placeholder="hello-world"
              />
            )}
          />

          {/* Identifier */}
          <Controller
            name="identifier"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Identifier"
                fullWidth
                error={!!errors.identifier}
                helperText={errors.identifier?.message || 'Hierarchical identifier with dots (e.g., python.basics.hello.world)'}
                placeholder="python.basics.hello.world"
              />
            )}
          />

          {/* Title */}
          <Controller
            name="title"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Title"
                fullWidth
                error={!!errors.title}
                helperText={errors.title?.message}
                placeholder="Hello World Example"
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
                rows={3}
                placeholder="A simple hello world program to introduce basic programming concepts"
              />
            )}
          />

          {/* Subject and Category */}
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Controller
              name="subject"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Subject"
                  fullWidth
                  placeholder="python"
                  helperText="Programming language or subject area"
                />
              )}
            />

            <Controller
              name="category"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Category"
                  fullWidth
                  placeholder="basics"
                  helperText="Category for grouping examples"
                />
              )}
            />
          </Box>

          {/* Tags */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Tags
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
              <TextField
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Add a tag"
                size="small"
                sx={{ flexGrow: 1 }}
              />
              <IconButton onClick={handleAddTag} size="small">
                <AddIcon />
              </IconButton>
            </Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {watchedTags.map((tag, index) => (
                <Chip
                  key={index}
                  label={tag}
                  size="small"
                  onDelete={() => handleRemoveTag(tag)}
                  deleteIcon={<CloseIcon />}
                />
              ))}
            </Box>
          </Box>

          {/* Version Identifier */}
          <Controller
            name="version_identifier"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Version Identifier"
                fullWidth
                placeholder="v1.0 or commit hash"
                helperText="Optional version identifier for change detection"
              />
            )}
          />
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

export default ExampleForm;