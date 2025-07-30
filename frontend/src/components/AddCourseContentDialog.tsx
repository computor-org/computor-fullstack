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
  ArrowRight as ArrowRightIcon,
  SubdirectoryArrowRight as SubdirectoryArrowRightIcon,
} from '@mui/icons-material';
import { apiClient } from '../services/apiClient';
import { CourseContentGet, CourseContentCreate, CourseContentTypeGet, CourseContentKindGet } from '../types/generated/courses';

interface AddCourseContentDialogProps {
  open: boolean;
  onClose: () => void;
  courseId: string;
  existingContent: CourseContentGet[];
  onContentAdded: () => void;
}

const AddCourseContentDialog: React.FC<AddCourseContentDialogProps> = ({
  open,
  onClose,
  courseId,
  existingContent,
  onContentAdded,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contentTypes, setContentTypes] = useState<CourseContentTypeGet[]>([]);
  const [contentKinds, setContentKinds] = useState<CourseContentKindGet[]>([]);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    parent: '',
    contentTypeId: '',
    position: 10,
  });

  const [selectedParent, setSelectedParent] = useState<CourseContentGet | null>(null);
  const [selectedContentType, setSelectedContentType] = useState<CourseContentTypeGet | null>(null);

  // Load content types and kinds
  useEffect(() => {
    if (open) {
      loadContentTypes();
      loadContentKinds();
    }
  }, [open, courseId]);

  const loadContentTypes = async () => {
    try {
      const response = await apiClient.get<CourseContentTypeGet[]>('/course-content-types', {
        params: {
          course_id: courseId,
          limit: 100,
        },
      });
      const data = Array.isArray(response) ? response : (response as any).data || [];
      setContentTypes(data);
    } catch (err) {
      console.error('Error loading content types:', err);
    }
  };

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

  // Filter available parents based on selected content type
  const getAvailableParents = () => {
    if (!selectedContentType || !selectedContentType.course_content_kind) {
      return existingContent;
    }

    const selectedKind = selectedContentType.course_content_kind;
    
    // If this kind doesn't allow ascendants, it can only be at root level
    if (!selectedKind.has_ascendants) {
      return [];
    }

    // Filter parents that allow descendants
    return existingContent.filter(content => {
      const contentType = contentTypes.find(ct => ct.id === content.course_content_type_id);
      if (!contentType || !contentType.course_content_kind) return false;
      return contentType.course_content_kind.has_descendants;
    });
  };

  const generatePath = () => {
    const baseTitle = formData.title || 'untitled';
    const pathSegment = baseTitle.toLowerCase().replace(/[^a-z0-9]/g, '_');
    
    if (!selectedParent) {
      return pathSegment;
    }
    
    return `${selectedParent.path}.${pathSegment}`;
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!formData.title || !formData.contentTypeId) {
        setError('Title and Content Type are required');
        return;
      }

      const path = generatePath();

      const newContent: CourseContentCreate = {
        title: formData.title,
        description: formData.description || undefined,
        path,
        course_id: courseId,
        course_content_type_id: formData.contentTypeId,
        version_identifier: 'initial',
        position: formData.position,
        max_group_size: 1,
      };

      await apiClient.post('/course-contents', newContent);
      
      onContentAdded();
      handleClose();
    } catch (err: any) {
      console.error('Error creating content:', err);
      setError(err.message || 'Failed to create content');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      title: '',
      description: '',
      parent: '',
      contentTypeId: '',
      position: 10,
    });
    setSelectedParent(null);
    setSelectedContentType(null);
    setError(null);
    onClose();
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

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Course Content</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {contentTypes.length === 0 && (
            <Alert severity="info">
              No content types available. Please create content types first using the "Manage Types" button.
            </Alert>
          )}

          <FormControl fullWidth required>
            <InputLabel>Content Type</InputLabel>
            <Select
              value={formData.contentTypeId}
              onChange={(e) => {
                const typeId = e.target.value;
                const type = contentTypes.find(ct => ct.id === typeId);
                setFormData({ ...formData, contentTypeId: typeId });
                setSelectedContentType(type || null);
              }}
              label="Content Type"
            >
              {contentTypes.map((type) => (
                <MenuItem key={type.id} value={type.id}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Box sx={{ color: type.color || 'action.active' }}>
                      {type.course_content_kind && getContentIcon(type.course_content_kind.id)}
                    </Box>
                    <Typography>{type.title || type.slug}</Typography>
                    {type.course_content_kind && (
                      <Chip
                        label={type.course_content_kind.id}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Stack>
                </MenuItem>
              ))}
            </Select>
            {selectedContentType && selectedContentType.course_content_kind && (
              <FormHelperText>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {selectedContentType.course_content_kind.submittable && (
                    <Chip label="Submittable" size="small" color="info" variant="outlined" />
                  )}
                  {selectedContentType.course_content_kind.has_ascendants ? (
                    <Chip label="Can have parent" size="small" color="success" variant="outlined" />
                  ) : (
                    <Chip label="Must be at root level" size="small" color="warning" variant="outlined" />
                  )}
                  {selectedContentType.course_content_kind.has_descendants ? (
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
            required
          />

          <TextField
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            fullWidth
            multiline
            rows={3}
          />

          {selectedContentType && selectedContentType.course_content_kind?.has_ascendants && (
            <FormControl fullWidth>
              <InputLabel>Parent (Optional)</InputLabel>
              <Select
                value={formData.parent}
                onChange={(e) => {
                  const parentId = e.target.value;
                  const parent = existingContent.find(c => c.id === parentId);
                  setFormData({ ...formData, parent: parentId });
                  setSelectedParent(parent || null);
                }}
                label="Parent (Optional)"
              >
                <MenuItem value="">
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Box sx={{ width: 24 }} />
                    <Typography color="text.secondary" fontStyle="italic">
                      None (Root level)
                    </Typography>
                  </Stack>
                </MenuItem>
                {getAvailableParents()
                  .sort((a, b) => {
                    // Sort by path to maintain hierarchy
                    return a.path.localeCompare(b.path);
                  })
                  .map((content) => {
                    const depth = content.path.split('.').length - 1;
                    const contentType = contentTypes.find(ct => ct.id === content.course_content_type_id);
                    const contentKind = contentType?.course_content_kind;
                    
                    return (
                      <MenuItem key={content.id} value={content.id}>
                        <Stack direction="row" spacing={1} alignItems="center" sx={{ width: '100%' }}>
                          <Box sx={{ ml: depth * 3, display: 'flex', alignItems: 'center' }}>
                            {depth > 0 && <SubdirectoryArrowRightIcon fontSize="small" color="action" />}
                            <Box sx={{ color: contentType?.color || 'action.active', ml: 0.5 }}>
                              {contentKind && getContentIcon(contentKind.id)}
                            </Box>
                          </Box>
                          <Typography>
                            {content.title || content.path}
                          </Typography>
                          {contentKind && !contentKind.has_descendants && (
                            <Chip 
                              label="Cannot have children" 
                              size="small" 
                              color="warning"
                              variant="outlined"
                              sx={{ ml: 'auto' }}
                            />
                          )}
                        </Stack>
                      </MenuItem>
                    );
                  })}
              </Select>
            </FormControl>
          )}

          <TextField
            label="Position"
            type="number"
            value={formData.position}
            onChange={(e) => setFormData({ ...formData, position: parseInt(e.target.value) || 0 })}
            fullWidth
            helperText="Order within the same level (lower numbers appear first)"
          />

          {formData.title && (
            <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Hierarchy Preview
              </Typography>
              <Stack spacing={1}>
                {selectedParent && (
                  <>
                    {/* Show parent hierarchy */}
                    {(() => {
                      const parentParts = selectedParent.path.split('.');
                      return parentParts.map((part, index) => {
                        const isLast = index === parentParts.length - 1;
                        const parentContentAtLevel = existingContent.find(c => 
                          c.path === parentParts.slice(0, index + 1).join('.')
                        );
                        
                        return (
                          <Stack key={index} direction="row" spacing={1} alignItems="center" sx={{ ml: index * 3 }}>
                            {index > 0 && <SubdirectoryArrowRightIcon fontSize="small" color="action" />}
                            <Typography variant="body2" color={isLast ? "text.primary" : "text.secondary"}>
                              {parentContentAtLevel?.title || part}
                            </Typography>
                          </Stack>
                        );
                      });
                    })()}
                  </>
                )}
                
                {/* Show new content */}
                <Stack 
                  direction="row" 
                  spacing={1} 
                  alignItems="center" 
                  sx={{ 
                    ml: selectedParent ? (selectedParent.path.split('.').length) * 3 : 0,
                    p: 1,
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    borderRadius: 1,
                  }}
                >
                  {selectedParent && <SubdirectoryArrowRightIcon fontSize="small" />}
                  <Box sx={{ color: 'inherit' }}>
                    {selectedContentType && getContentIcon(selectedContentType.course_content_kind?.id || 'folder')}
                  </Box>
                  <Typography variant="body2" fontWeight="bold">
                    {formData.title} (New)
                  </Typography>
                </Stack>
                
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                  Path: <code>{generatePath()}</code>
                </Typography>
              </Stack>
            </Box>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !formData.title || !formData.contentTypeId}
          startIcon={loading && <CircularProgress size={20} />}
        >
          Add Content
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddCourseContentDialog;