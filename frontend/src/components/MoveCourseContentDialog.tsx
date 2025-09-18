import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Stack,
  Typography,
  Box,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  Folder as FolderIcon,
  Assignment as AssignmentIcon,
  School as SchoolIcon,
  SubdirectoryArrowRight as SubdirectoryArrowRightIcon,
  Warning as WarningIcon,
  MoveDown as MoveDownIcon,
} from '@mui/icons-material';
import { apiClient } from '../services/apiClient';
import { CourseContentGet, CourseContentUpdate, CourseContentTypeGet, CourseContentKindGet } from '../types/generated/courses';

interface MoveCourseContentDialogProps {
  open: boolean;
  onClose: () => void;
  content: CourseContentGet | null;
  allContent: CourseContentGet[];
  contentTypes: CourseContentTypeGet[];
  contentKinds: CourseContentKindGet[];
  onContentMoved: () => Promise<void> | void;
}

const MoveCourseContentDialog: React.FC<MoveCourseContentDialogProps> = ({
  open,
  onClose,
  content,
  allContent,
  contentTypes,
  contentKinds,
  onContentMoved,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedParent, setSelectedParent] = useState<string>('');
  const [newPath, setNewPath] = useState<string>('');

  useEffect(() => {
    if (content) {
      // Set current parent
      const pathParts = content.path.split('.');
      if (pathParts.length > 1) {
        const parentPath = pathParts.slice(0, -1).join('.');
        const parent = allContent.find(c => c.path === parentPath);
        setSelectedParent(parent?.id || '');
      } else {
        setSelectedParent('');
      }
    }
  }, [content, allContent]);

  // Get all children of the content being moved
  const getDescendants = (item: CourseContentGet): CourseContentGet[] => {
    return allContent.filter(c => 
      c.path.startsWith(item.path + '.') && c.id !== item.id
    );
  };

  // Get valid parent options (cannot move to self or descendants)
  const getValidParents = () => {
    if (!content) return [];

    const descendants = getDescendants(content);
    const descendantIds = new Set(descendants.map(d => d.id));
    
    // Get content type and kind for the content being moved
    const contentType = contentTypes.find(ct => ct.id === content.course_content_type_id);
    const contentKind = contentType ? contentKinds.find(k => k.id === contentType.course_content_kind_id) : null;
    
    // Filter out invalid parents
    return allContent.filter(item => {
      // Cannot move to self
      if (item.id === content.id) return false;
      
      // Cannot move to descendants
      if (descendantIds.has(item.id)) return false;
      
      // Check if this content type can have a parent
      if (contentKind && !contentKind.has_ascendants && item.id !== '') return false;
      
      // Check if the potential parent can have children
      const parentType = contentTypes.find(ct => ct.id === item.course_content_type_id);
      const parentKind = parentType ? contentKinds.find(k => k.id === parentType.course_content_kind_id) : null;
      if (parentKind && !parentKind.has_descendants) return false;
      
      return true;
    });
  };

  const getContentIcon = (kindId: string) => {
    switch (kindId) {
      case 'unit':
        return <SchoolIcon fontSize="small" />;
      case 'assignment':
        return <AssignmentIcon fontSize="small" />;
      default:
        return <FolderIcon fontSize="small" />;
    }
  };

  const generateNewPath = () => {
    if (!content) return '';
    
    const pathParts = content.path.split('.');
    const lastSegment = pathParts[pathParts.length - 1];
    
    if (!selectedParent) {
      return lastSegment;
    }
    
    const parent = allContent.find(c => c.id === selectedParent);
    if (!parent) return lastSegment;
    
    return `${parent.path}.${lastSegment}`;
  };

  useEffect(() => {
    setNewPath(generateNewPath());
  }, [selectedParent, content]);

  const handleMove = async () => {
    if (!content) return;

    try {
      setLoading(true);
      setError(null);

      const updateData: CourseContentUpdate = {
        path: newPath,
      };

      await apiClient.patch(`/course-contents/${content.id}`, updateData);

      await onContentMoved();
      handleClose();
    } catch (err: any) {
      console.error('Error moving content:', err);
      setError(err.message || 'Failed to move content. The backend might not support path updates yet.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSelectedParent('');
    setNewPath('');
    setError(null);
    onClose();
  };

  if (!content) return null;

  const descendants = getDescendants(content);
  const validParents = getValidParents();

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Stack direction="row" spacing={1} alignItems="center">
          <MoveDownIcon />
          <Typography>Move Course Content</Typography>
        </Stack>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Current Location */}
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Current Location
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="body1" fontWeight="bold">
                {content.title || content.path}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Path: <code>{content.path}</code>
              </Typography>
            </Box>
          </Box>

          {/* New Parent Selection */}
          <FormControl fullWidth>
            <InputLabel>New Parent Location</InputLabel>
            <Select
              value={selectedParent}
              onChange={(e) => setSelectedParent(e.target.value)}
              label="New Parent Location"
            >
              <MenuItem value="">
                <Stack direction="row" spacing={1} alignItems="center">
                  <Box sx={{ width: 24 }} />
                  <Typography color="text.secondary" fontStyle="italic">
                    Root level (no parent)
                  </Typography>
                </Stack>
              </MenuItem>
              {validParents
                .sort((a, b) => a.path.localeCompare(b.path))
                .map((item) => {
                  const depth = item.path.split('.').length - 1;
                  const contentType = contentTypes.find(ct => ct.id === item.course_content_type_id);
                  
                  return (
                    <MenuItem key={item.id} value={item.id}>
                      <Stack direction="row" spacing={1} alignItems="center" sx={{ width: '100%' }}>
                        <Box sx={{ ml: depth * 3, display: 'flex', alignItems: 'center' }}>
                          {depth > 0 && <SubdirectoryArrowRightIcon fontSize="small" color="action" />}
                          <Box sx={{ color: contentType?.color || 'action.active', ml: 0.5 }}>
                            {contentType && getContentIcon(contentType.course_content_kind_id)}
                          </Box>
                        </Box>
                        <Typography>
                          {item.title || item.path}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                          {item.path}
                        </Typography>
                      </Stack>
                    </MenuItem>
                  );
                })}
            </Select>
          </FormControl>

          {/* New Path Preview */}
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              New Path Preview
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'primary.contrastText', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight="bold">
                {newPath}
              </Typography>
            </Box>
          </Box>

          {/* Warnings */}
          {descendants.length > 0 && (
            <Alert severity="warning" icon={<WarningIcon />}>
              <Typography variant="body2" fontWeight="bold" gutterBottom>
                This will also move {descendants.length} child item{descendants.length > 1 ? 's' : ''}:
              </Typography>
              <Box sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
                {descendants.slice(0, 5).map((child) => (
                  <Typography key={child.id} variant="caption" display="block">
                    • {child.title || child.path}
                  </Typography>
                ))}
                {descendants.length > 5 && (
                  <Typography variant="caption" color="text.secondary">
                    ... and {descendants.length - 5} more
                  </Typography>
                )}
              </Box>
            </Alert>
          )}

          <Alert severity="info">
            <Typography variant="body2">
              Moving content will update its path and the paths of all its children. 
              This operation cannot be undone easily.
            </Typography>
          </Alert>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleMove}
          variant="contained"
          disabled={loading || newPath === content.path}
          startIcon={loading ? <CircularProgress size={20} /> : <MoveDownIcon />}
        >
          Move Content
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MoveCourseContentDialog;
