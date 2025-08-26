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
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Tabs,
  Tab,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Assignment as AssignmentIcon,
  School as SchoolIcon,
  Circle as CircleIcon,
} from '@mui/icons-material';
import { apiClient } from '../services/apiClient';
import { CourseContentTypeGet, CourseContentKindGet, CourseContentTypeCreate } from '../types/generated/courses';

interface ManageCourseContentTypesDialogProps {
  open: boolean;
  onClose: () => void;
  courseId: string;
  onTypesChanged?: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

const ManageCourseContentTypesDialog: React.FC<ManageCourseContentTypesDialogProps> = ({
  open,
  onClose,
  courseId,
  onTypesChanged,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  
  // Data
  const [contentTypes, setContentTypes] = useState<CourseContentTypeGet[]>([]);
  const [contentKinds, setContentKinds] = useState<CourseContentKindGet[]>([]);
  
  // Create form state
  const [createForm, setCreateForm] = useState({
    contentKindId: '',
    title: '',
    slug: '',
    description: '',
    color: '#2196f3',
  });

  // Load data when dialog opens
  useEffect(() => {
    if (open) {
      loadContentTypes();
      loadContentKinds();
      // Reset form when opening
      setCreateForm({
        contentKindId: '',
        title: '',
        slug: '',
        description: '',
        color: '#2196f3',
      });
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

  const generateSlug = (title: string) => {
    return title.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
  };

  const handleTitleChange = (title: string) => {
    setCreateForm({
      ...createForm,
      title,
      slug: generateSlug(title),
    });
  };

  const handleCreateSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!createForm.contentKindId || !createForm.title || !createForm.slug) {
        setError('Please fill in all required fields');
        return;
      }

      const newType: CourseContentTypeCreate = {
        course_id: courseId,
        course_content_kind_id: createForm.contentKindId,
        title: createForm.title,
        slug: createForm.slug,
        description: createForm.description || undefined,
        color: createForm.color,
      };

      await apiClient.post('/course-content-types', newType);
      
      // Reload content types
      await loadContentTypes();
      
      // Reset form
      setCreateForm({
        contentKindId: '',
        title: '',
        slug: '',
        description: '',
        color: '#2196f3',
      });
      
      // Notify parent
      if (onTypesChanged) {
        onTypesChanged();
      }
      
      // Switch to list tab
      setTabValue(0);
    } catch (err: any) {
      console.error('Error creating content type:', err);
      setError(err.message || 'Failed to create content type');
    } finally {
      setLoading(false);
    }
  };

  const getKindIcon = (kindId: string) => {
    switch (kindId) {
      case 'assignment':
        return <AssignmentIcon fontSize="small" />;
      case 'unit':
        return <SchoolIcon fontSize="small" />;
      default:
        return <CircleIcon fontSize="small" />;
    }
  };

  const getKindInfo = (kind: CourseContentKindGet) => {
    const features = [];
    if (kind.submittable) features.push('Submittable');
    if (kind.has_ascendants) features.push('Can have parent');
    if (kind.has_descendants) features.push('Can have children');
    return features.join(' • ');
  };

  const handleClose = () => {
    setTabValue(0);
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Manage Course Content Types</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={`Content Types (${contentTypes.length})`} />
          <Tab label="Create New" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Content types define how different kinds of content appear in your course.
          </Typography>
          
          <List>
            {contentTypes.length === 0 ? (
              <ListItem>
                <ListItemText 
                  primary="No content types yet"
                  secondary="Create your first content type to start organizing course content"
                />
              </ListItem>
            ) : (
              contentTypes.map((type) => (
                <React.Fragment key={type.id}>
                  <ListItem>
                    <Box sx={{ mr: 2, color: type.color || 'action.active' }}>
                      {type.course_content_kind && getKindIcon(type.course_content_kind.id)}
                    </Box>
                    <ListItemText
                      primary={
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography>{type.title || type.slug}</Typography>
                          <Chip
                            label={type.slug}
                            size="small"
                            sx={{
                              backgroundColor: type.color || 'action.selected',
                              color: 'white',
                            }}
                          />
                        </Stack>
                      }
                      secondary={
                        <Stack spacing={0.5}>
                          {type.description && (
                            <Typography variant="body2">{type.description}</Typography>
                          )}
                          {type.course_content_kind && (
                            <Typography variant="caption" color="text.secondary">
                              Kind: {type.course_content_kind.title} • {getKindInfo(type.course_content_kind)}
                            </Typography>
                          )}
                        </Stack>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton edge="end" size="small">
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton edge="end" size="small">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))
            )}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Stack spacing={3}>
            <Typography variant="body2" color="text.secondary">
              Create a new content type for your course based on available content kinds.
            </Typography>

            {contentKinds.length === 0 && (
              <Alert severity="warning">
                No content kinds available. Please check the API endpoint or database initialization.
              </Alert>
            )}

            <FormControl fullWidth required>
              <InputLabel>Content Kind</InputLabel>
              <Select
                value={createForm.contentKindId}
                onChange={(e) => setCreateForm({ ...createForm, contentKindId: e.target.value })}
                label="Content Kind"
              >
                {contentKinds.map((kind) => (
                  <MenuItem key={kind.id} value={kind.id}>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ width: '100%' }}>
                      <Box>{getKindIcon(kind.id)}</Box>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography>{kind.title}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {getKindInfo(kind)}
                        </Typography>
                      </Box>
                    </Stack>
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>
                Choose the base type that defines the behavior of this content
              </FormHelperText>
            </FormControl>

            <TextField
              label="Display Title"
              value={createForm.title}
              onChange={(e) => handleTitleChange(e.target.value)}
              fullWidth
              required
              helperText="How this content type appears in your course"
            />

            <TextField
              label="Slug"
              value={createForm.slug}
              onChange={(e) => setCreateForm({ ...createForm, slug: e.target.value })}
              fullWidth
              required
              helperText="URL-friendly identifier (auto-generated from title)"
              InputProps={{
                startAdornment: <InputAdornment position="start">course-content/</InputAdornment>,
              }}
            />

            <TextField
              label="Description"
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              fullWidth
              multiline
              rows={2}
              helperText="Optional description for this content type"
            />

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Color
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center">
                <input
                  type="color"
                  value={createForm.color}
                  onChange={(e) => setCreateForm({ ...createForm, color: e.target.value })}
                  style={{ width: 50, height: 40, border: '1px solid #ccc', borderRadius: 4 }}
                />
                <TextField
                  value={createForm.color}
                  onChange={(e) => setCreateForm({ ...createForm, color: e.target.value })}
                  size="small"
                  sx={{ width: 120 }}
                />
                <Typography variant="body2" color="text.secondary">
                  Color for visual identification
                </Typography>
              </Stack>
            </Box>

            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                onClick={handleCreateSubmit}
                disabled={loading || !createForm.contentKindId || !createForm.title}
                startIcon={loading ? <CircularProgress size={20} /> : <AddIcon />}
              >
                Create Content Type
              </Button>
            </Box>
          </Stack>
        </TabPanel>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ManageCourseContentTypesDialog;