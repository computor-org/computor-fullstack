import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Stack,
  Typography,
  Box,
  CircularProgress,
  Chip,
  FormHelperText,
} from '@mui/material';
import {
  Folder as FolderIcon,
  Assignment as AssignmentIcon,
  Quiz as QuizIcon,
  MenuBook as MenuBookIcon,
  School as SchoolIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { apiClient } from '../services/apiClient';
import { CourseContentGet, CourseContentUpdate, CourseContentTypeGet, CourseContentKindGet } from '../types/generated/courses';

interface EditCourseContentDialogProps {
  open: boolean;
  onClose: () => void;
  content: CourseContentGet | null;
  contentTypes: CourseContentTypeGet[];
  onContentUpdated: () => void;
}

const EditCourseContentDialog: React.FC<EditCourseContentDialogProps> = ({
  open,
  onClose,
  content,
  contentTypes,
  onContentUpdated,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contentKinds, setContentKinds] = useState<CourseContentKindGet[]>([]);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    contentTypeId: '',
    position: 10,
  });

  // Load content kinds
  useEffect(() => {
    if (open) {
      loadContentKinds();
    }
  }, [open]);

  // Update form when content changes
  useEffect(() => {
    if (content) {
      setFormData({
        title: content.title || '',
        description: content.description || '',
        contentTypeId: content.course_content_type_id,
        position: content.position,
      });
    }
  }, [content]);

  const loadContentKinds = async () => {
    try {
      const response = await apiClient.get<CourseContentKindGet[]>('/course-content-kinds', {
        params: {
          limit: 100,
        },
      });
      const data = Array.isArray(response) ? response : (response as any).data || [];
      setContentKinds(data);
    } catch (err) {
      console.error('Error loading content kinds:', err);
    }
  };

  const getContentIcon = (kind: string) => {
    switch (kind) {
      case 'unit':
        return <SchoolIcon fontSize="small" />;
      case 'folder':
        return <FolderIcon fontSize="small" />;
      case 'assignment':
        return <AssignmentIcon fontSize="small" />;
      case 'quiz':
        return <QuizIcon fontSize="small" />;
      case 'reading':
      case 'lecture':
        return <MenuBookIcon fontSize="small" />;
      default:
        return <FolderIcon fontSize="small" />;
    }
  };

  const handleSubmit = async () => {
    if (!content) return;

    try {
      setLoading(true);
      setError(null);

      const updateData: CourseContentUpdate = {
        title: formData.title || undefined,
        description: formData.description || undefined,
        position: formData.position,
      };

      // Check if content type changed
      if (formData.contentTypeId !== content.course_content_type_id) {
        // Verify the new content type has the same kind
        const newContentType = contentTypes.find(ct => ct.id === formData.contentTypeId);
        const oldContentType = contentTypes.find(ct => ct.id === content.course_content_type_id);
        
        if (newContentType && oldContentType) {
          if (newContentType.course_content_kind_id !== oldContentType.course_content_kind_id) {
            setError('Cannot change to a content type with a different kind.');
            setLoading(false);
            return;
          }
          
          // Include content type change in update
          updateData.course_content_type_id = formData.contentTypeId;
        }
      }

      await apiClient.patch(`/course-contents/${content.id}`, updateData);
      
      onContentUpdated();
      handleClose();
    } catch (err: any) {
      console.error('Error updating content:', err);
      setError(err.message || 'Failed to update content');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      title: '',
      description: '',
      contentTypeId: '',
      position: 10,
    });
    setError(null);
    onClose();
  };

  const selectedContentType = content ? contentTypes.find(ct => ct.id === content.course_content_type_id) : null;
  const selectedKind = selectedContentType 
    ? contentKinds.find(k => k.id === selectedContentType.course_content_kind_id)
    : null;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit Course Content</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {content && (
            <Alert severity="info" icon={<WarningIcon />}>
              <Typography variant="body2">
                Path: <code>{content.path}</code>
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Note: You cannot change the path or parent of existing content. To move content, you need to delete and recreate it.
              </Typography>
            </Alert>
          )}

          <FormControl fullWidth>
            <InputLabel>Content Type</InputLabel>
            <Select
              value={formData.contentTypeId}
              onChange={(e) => setFormData({ ...formData, contentTypeId: e.target.value })}
              label="Content Type"
            >
              {contentTypes
                .filter(type => {
                  // Only show content types with the same kind
                  const currentContentType = content ? contentTypes.find(ct => ct.id === content.course_content_type_id) : null;
                  if (!currentContentType) return true;
                  return type.course_content_kind_id === currentContentType.course_content_kind_id;
                })
                .map((type) => (
                  <MenuItem key={type.id} value={type.id}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Box sx={{ color: type.color || 'action.active' }}>
                        {getContentIcon(type.course_content_kind_id)}
                      </Box>
                      <Typography>{type.title || type.slug}</Typography>
                      <Chip
                        label={type.course_content_kind_id}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                  </MenuItem>
                ))
              }
            </Select>
            {selectedKind && (
              <FormHelperText>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  <Typography variant="caption" color="text.secondary">
                    Only showing types with kind: {selectedKind.id}
                  </Typography>
                  {selectedKind.submittable && (
                    <Chip label="Submittable" size="small" color="info" variant="outlined" />
                  )}
                  {selectedKind.has_descendants ? (
                    <Chip label="Can have children" size="small" color="success" variant="outlined" />
                  ) : (
                    <Chip label="Cannot have children" size="small" color="warning" variant="outlined" />
                  )}
                </Stack>
              </FormHelperText>
            )}
          </FormControl>

          <TextField
            label="Title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            fullWidth
          />

          <TextField
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            fullWidth
            multiline
            rows={3}
          />

          <TextField
            label="Position"
            type="number"
            value={formData.position}
            onChange={(e) => setFormData({ ...formData, position: parseInt(e.target.value) || 0 })}
            fullWidth
            helperText="Order within the same level (lower numbers appear first)"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !formData.title}
          startIcon={loading && <CircularProgress size={20} />}
        >
          Update Content
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default EditCourseContentDialog;