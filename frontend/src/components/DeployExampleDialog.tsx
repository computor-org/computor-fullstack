import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Stack,
  Chip,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
import {
  Search as SearchIcon,
  CloudUpload as CloudUploadIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Code as CodeIcon,
  Category as CategoryIcon,
  Label as LabelIcon,
  Refresh as RefreshIcon,
  Preview as PreviewIcon,
} from '@mui/icons-material';
import { apiClient } from '../services/apiClient';
import { CourseContentGet } from '../types/generated/courses';
import { ExampleList } from '../types/generated/examples';

interface DeploymentPreview {
  example: {
    id: string;
    title: string;
    description?: string;
    category?: string;
    language?: string;
  };
  version?: {
    id: string;
    version_tag: string;
    created_at: string;
  };
  dependencies: Array<{
    example_id: string;
    title: string;
    required: boolean;
  }>;
  conflicts: Array<{
    type: string;
    path: string;
    current_content?: string;
    current_example_id?: string;
    current_example_version?: string;
  }>;
  file_structure: {
    files: string[];
    size_mb: number;
  };
}

interface DeployExampleDialogProps {
  open: boolean;
  onClose: () => void;
  courseId: string;
  content: CourseContentGet;
  onDeploymentStarted: () => Promise<void> | void;
}

const DeployExampleDialog: React.FC<DeployExampleDialogProps> = ({
  open,
  onClose,
  courseId,
  content,
  onDeploymentStarted,
}) => {
  const [loading, setLoading] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');
  const [examples, setExamples] = useState<ExampleList[]>([]);
  const [filters, setFilters] = useState<{ categories: string[]; languages: string[] }>({
    categories: [],
    languages: [],
  });
  const [selectedExample, setSelectedExample] = useState<ExampleList | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<string>('latest');
  const [preview, setPreview] = useState<DeploymentPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  // Load available examples
  const loadExamples = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {};
      if (searchQuery) params.search = searchQuery;
      if (selectedCategory) params.category = selectedCategory;
      // Language filtering not available

      // Fetch examples from the standard examples endpoint
      const examplesData = await apiClient.get<ExampleList[]>('/examples', { params });

      setExamples(examplesData || []);
      
      // Extract unique categories and languages from the examples
      const categories = new Set<string>();
      const languages = new Set<string>();
      
      examplesData.forEach(example => {
        if (example.category) categories.add(example.category);
        // Language is not available in ExampleList
      });
      
      setFilters({
        categories: Array.from(categories).sort(),
        languages: [] // Language filtering not available
      });
    } catch (err: any) {
      console.error('Error loading examples:', err);
      setError(err.message || 'Failed to load examples');
    } finally {
      setLoading(false);
    }
  };

  // Load deployment preview
  const loadPreview = async (example: ExampleList) => {
    try {
      setLoadingPreview(true);
      setError(null);

      // For now, create a simple preview based on the example data
      // In the future, this could call a preview endpoint
      const preview: DeploymentPreview = {
        example: {
          id: example.id,
          title: example.title,
          description: example.subject || undefined,
          category: example.category || undefined,
          language: undefined, // Not available in ExampleList
        },
        version: {
          id: example.id,
          version_tag: selectedVersion,
          created_at: example.created_at || new Date().toISOString(),
        },
        dependencies: [],
        conflicts: [],
        file_structure: {
          files: ['meta.yaml', 'README.md'],
          size_mb: 0.1,
        },
      };
      
      setPreview(preview);
    } catch (err: any) {
      console.error('Error loading preview:', err);
      setError(err.message || 'Failed to load deployment preview');
    } finally {
      setLoadingPreview(false);
    }
  };

  // Deploy example
  const handleDeploy = async () => {
    if (!selectedExample) return;

    try {
      setDeploying(true);
      setError(null);

      // Use the new two-step process: assign example to course content
      const response = await apiClient.post<{
        id: string;
        deployment_status: string;
      }>(`/course-contents/${content.id}/assign-example`, {
        example_id: selectedExample.id,
        example_version: selectedVersion,
      });

      setSuccess(true);
      setTimeout(async () => {
        await onDeploymentStarted();
        onClose();
      }, 1500);
    } catch (err: any) {
      console.error('Error deploying example:', err);
      setError(err.message || 'Failed to deploy example');
    } finally {
      setDeploying(false);
    }
  };

  useEffect(() => {
    if (open) {
      loadExamples();
      setSelectedExample(null);
      setPreview(null);
      setTabValue(0);
      setSuccess(false);
    }
  }, [open]);

  useEffect(() => {
    if (selectedExample) {
      loadPreview(selectedExample);
    }
  }, [selectedExample, selectedVersion]);

  const filteredExamples = examples.filter((example) => {
    const matchesSearch =
      !searchQuery ||
      example.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (example.subject || '').toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = !selectedCategory || example.category === selectedCategory;
    const matchesLanguage = true; // Language filtering not available
    
    return matchesSearch && matchesCategory && matchesLanguage;
  });

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' },
      }}
    >
      <DialogTitle>
        <Stack direction="row" alignItems="center" spacing={2}>
          <CloudUploadIcon />
          <Box>
            <Typography variant="h6">Assign Example to {content.title || content.path}</Typography>
            <Typography variant="caption" color="text.secondary">
              Select an example from the library to assign to this course content
            </Typography>
          </Box>
        </Stack>
      </DialogTitle>
      
      <DialogContent dividers sx={{ p: 0 }}>
        {success ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              p: 4,
            }}
          >
            <CheckIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Example Assigned!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              The example has been assigned to the course content.
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', height: '100%' }}>
            {/* Left Panel - Example Selection */}
            <Box sx={{ width: '50%', borderRight: 1, borderColor: 'divider', p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Example Library
              </Typography>
              
              {/* Search and Filters */}
              <Stack spacing={2} sx={{ mb: 3 }}>
                <TextField
                  size="small"
                  placeholder="Search examples..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
                
                <Stack direction="row" spacing={2}>
                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      label="Category"
                    >
                      <MenuItem value="">All Categories</MenuItem>
                      {filters.categories.map((cat) => (
                        <MenuItem key={cat} value={cat}>
                          {cat}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  {/* Language filtering not available in ExampleList */}
                  
                  <IconButton onClick={loadExamples} size="small">
                    <RefreshIcon />
                  </IconButton>
                </Stack>
              </Stack>
              
              {/* Example List */}
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : filteredExamples.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="text.secondary">
                    No examples found matching your criteria
                  </Typography>
                </Box>
              ) : (
                <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {filteredExamples.map((example) => (
                    <ListItem
                      key={example.id}
                      sx={{ mb: 1, p: 0 }}
                    >
                      <ListItemButton
                        selected={selectedExample?.id === example.id}
                        onClick={() => setSelectedExample(example)}
                        sx={{ borderRadius: 1 }}
                      >
                        <ListItemText
                        primary={example.title}
                        secondary={
                          <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                            {example.category && (
                              <Chip
                                icon={<CategoryIcon />}
                                label={example.category}
                                size="small"
                                variant="outlined"
                              />
                            )}
                            {/* Language not available in ExampleList */}
                            {example.tags?.slice(0, 2).map((tag: string) => (
                              <Chip
                                key={tag}
                                icon={<LabelIcon />}
                                label={tag}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                          </Stack>
                        }
                      />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
            
            {/* Right Panel - Preview */}
            <Box sx={{ width: '50%', p: 3 }}>
              {selectedExample ? (
                <>
                  <Typography variant="h6" gutterBottom>
                    Deployment Preview
                  </Typography>
                  
                  {loadingPreview ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                      <CircularProgress />
                    </Box>
                  ) : preview ? (
                    <Box>
                      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
                        <Tab label="Overview" />
                        <Tab label="Files" />
                        <Tab label="Conflicts" />
                      </Tabs>
                      
                      {tabValue === 0 && (
                        <Box>
                          <Card sx={{ mb: 2 }}>
                            <CardContent>
                              <Typography variant="h6" gutterBottom>
                                {preview.example.title}
                              </Typography>
                              {preview.example.description && (
                                <Typography variant="body2" color="text.secondary" paragraph>
                                  {preview.example.description}
                                </Typography>
                              )}
                              <Stack direction="row" spacing={2}>
                                <Typography variant="body2">
                                  <strong>Version:</strong> {preview.version?.version_tag || 'latest'}
                                </Typography>
                                <Typography variant="body2">
                                  <strong>Target Path:</strong> {content.path}
                                </Typography>
                              </Stack>
                            </CardContent>
                          </Card>
                          
                          {preview.dependencies.length > 0 && (
                            <Card sx={{ mb: 2 }}>
                              <CardContent>
                                <Typography variant="subtitle2" gutterBottom>
                                  Dependencies
                                </Typography>
                                {preview.dependencies.map((dep) => (
                                  <Chip
                                    key={dep.example_id}
                                    label={dep.title}
                                    size="small"
                                    sx={{ mr: 1, mb: 1 }}
                                  />
                                ))}
                              </CardContent>
                            </Card>
                          )}
                        </Box>
                      )}
                      
                      {tabValue === 1 && (
                        <Card>
                          <CardContent>
                            <Typography variant="subtitle2" gutterBottom>
                              Files to Deploy
                            </Typography>
                            <List dense>
                              {preview.file_structure.files.map((file) => (
                                <ListItem key={file}>
                                  <ListItemText primary={file} />
                                </ListItem>
                              ))}
                            </List>
                          </CardContent>
                        </Card>
                      )}
                      
                      {tabValue === 2 && (
                        <Box>
                          {preview.conflicts.length === 0 ? (
                            <Alert severity="success">
                              No conflicts detected - safe to deploy!
                            </Alert>
                          ) : (
                            preview.conflicts.map((conflict, index) => (
                              <Alert key={index} severity="warning" sx={{ mb: 2 }}>
                                <Typography variant="subtitle2">{conflict.type}</Typography>
                                <Typography variant="body2">
                                  Path: {conflict.path}
                                  {conflict.current_content && ` - Current: ${conflict.current_content}`}
                                </Typography>
                              </Alert>
                            ))
                          )}
                        </Box>
                      )}
                    </Box>
                  ) : null}
                </>
              ) : (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <PreviewIcon sx={{ fontSize: 80, color: 'action.disabled', mb: 2 }} />
                  <Typography color="text.secondary">
                    Select an example to preview deployment details
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        )}
        
        {error && (
          <Alert severity="error" sx={{ m: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} disabled={deploying}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleDeploy}
          disabled={!selectedExample || deploying || success}
          startIcon={deploying ? <CircularProgress size={20} /> : <CloudUploadIcon />}
        >
          {deploying ? 'Assigning...' : 'Assign Example'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeployExampleDialog;
