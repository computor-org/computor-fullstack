import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  Typography,
  Box,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Warning as WarningIcon,
  SubdirectoryArrowRight as SubdirectoryArrowRightIcon,
} from '@mui/icons-material';
import { apiClient } from '../services/apiClient';
import { CourseContentGet } from '../types/generated/courses';

interface DeleteCourseContentDialogProps {
  open: boolean;
  onClose: () => void;
  content: CourseContentGet | null;
  allContent: CourseContentGet[];
  onContentDeleted: () => Promise<void> | void;
}

const DeleteCourseContentDialog: React.FC<DeleteCourseContentDialogProps> = ({
  open,
  onClose,
  content,
  allContent,
  onContentDeleted,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [childContent, setChildContent] = useState<CourseContentGet[]>([]);

  // Find all children of the content to be deleted
  useEffect(() => {
    if (content) {
      const children = allContent.filter(item => 
        item.path.startsWith(content.path + '.') && 
        item.id !== content.id
      );
      setChildContent(children);
    }
  }, [content, allContent]);

  const handleDelete = async () => {
    if (!content) return;

    try {
      setLoading(true);
      setError(null);

      await apiClient.delete(`/course-contents/${content.id}`);

      await onContentDeleted();
      handleClose();
    } catch (err: any) {
      console.error('Error deleting content:', err);
      setError(err.message || 'Failed to delete content');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  if (!content) return null;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Delete Course Content</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight="bold">
            Are you sure you want to delete this content?
          </Typography>
        </Alert>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Content to delete:
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText', borderRadius: 1 }}>
            <Typography variant="body1" fontWeight="bold">
              {content.title || content.path}
            </Typography>
            <Typography variant="body2">
              Path: <code>{content.path}</code>
            </Typography>
            {content.description && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {content.description}
              </Typography>
            )}
          </Box>
        </Box>

        {childContent.length > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight="bold" gutterBottom>
              This will also delete {childContent.length} child item{childContent.length > 1 ? 's' : ''}:
            </Typography>
            <List dense>
              {childContent.map((child) => {
                const depth = child.path.split('.').length - content.path.split('.').length - 1;
                return (
                  <ListItem key={child.id} sx={{ pl: depth * 2 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <SubdirectoryArrowRightIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={child.title || child.path}
                      secondary={`Path: ${child.path}`}
                    />
                  </ListItem>
                );
              })}
            </List>
          </Alert>
        )}

        <Typography variant="body2" color="text.secondary">
          This action cannot be undone.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleDelete}
          variant="contained"
          color="error"
          disabled={loading}
          startIcon={loading && <CircularProgress size={20} />}
        >
          Delete{childContent.length > 0 ? ` (${childContent.length + 1} items)` : ''}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteCourseContentDialog;
