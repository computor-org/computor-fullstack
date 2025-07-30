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

      // Note: Content type cannot be changed after creation

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

          {selectedContentType && (
            <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Content Type (cannot be changed)
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center">
                <Box sx={{ color: selectedContentType.color || 'action.active' }}>
                  {getContentIcon(selectedContentType.course_content_kind_id)}
                </Box>
                <Typography>{selectedContentType.title || selectedContentType.slug}</Typography>
                <Chip
                  label={selectedContentType.course_content_kind_id}
                  size="small"
                  variant="outlined"
                />
              </Stack>
              {selectedKind && (
                <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 1 }}>
                  {selectedKind.submittable && (
                    <Chip label="Submittable" size="small" color="info" variant="outlined" />
                  )}
                  {selectedKind.has_descendants ? (
                    <Chip label="Can have children" size="small" color="success" variant="outlined" />
                  ) : (
                    <Chip label="Cannot have children" size="small" color="warning" variant="outlined" />
                  )}
                </Stack>
              )}
            </Box>
          )}

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