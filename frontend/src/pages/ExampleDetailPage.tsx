import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Grid,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Download as DownloadIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  ExpandMore as ExpandMoreIcon,
  CloudDownload as CloudDownloadIcon,
} from '@mui/icons-material';
import * as yaml from 'js-yaml';

import { ExampleGet, ExampleRepositoryGet, ExampleDownloadResponse, ExampleVersionGet } from '../types/generated/examples';
import { apiClient } from '../services/apiClient';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`example-tabpanel-${index}`}
      aria-labelledby={`example-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}


const ExampleDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [example, setExample] = useState<ExampleGet | null>(null);
  const [versions, setVersions] = useState<ExampleVersionGet[]>([]);
  const [fullVersionDetails, setFullVersionDetails] = useState<Record<string, ExampleVersionGet>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [loadingMetadata, setLoadingMetadata] = useState(false);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadExampleDetail();
      loadVersions();
    }
  }, [id]);

  // Load metadata after versions are loaded and select first version
  useEffect(() => {
    if (versions.length > 0) {
      // Auto-select the first version if none is selected
      if (!selectedVersionId) {
        setSelectedVersionId(versions[0].id);
      }
      loadAllVersionDetails();
    }
  }, [versions, selectedVersionId]);

  const loadExampleDetail = async () => {
    try {
      const data = await apiClient.get<ExampleGet>(`/examples/${id}`);
      setExample(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load example');
    }
  };

  const loadVersions = async () => {
    try {
      const data = await apiClient.get<ExampleVersionGet[]>(`/examples/${id}/versions`);
      setVersions(data);
    } catch (err) {
      console.error('Error loading versions:', err);
      setVersions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (versionId: string, versionTag: string) => {
    setDownloading(versionId);
    try {
      const response = await apiClient.get<ExampleDownloadResponse>(`/examples/download/${versionId}`);
      
      // Create a ZIP file with all the example files
      const JSZip = require('jszip');
      const zip = new JSZip();
      
      // Add all files to the ZIP
      for (const [filename, content] of Object.entries(response.files)) {
        zip.file(filename, content);
      }
      
      // Add meta.yaml and test.yaml if they exist
      if (response.meta_yaml) {
        zip.file('meta.yaml', response.meta_yaml);
      }
      if (response.test_yaml) {
        zip.file('test.yaml', response.test_yaml);
      }
      
      // Generate and download the ZIP
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      const downloadUrl = URL.createObjectURL(zipBlob);
      
      // Create temporary download link
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${example?.directory || 'example'}-${versionTag}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up
      URL.revokeObjectURL(downloadUrl);
      
    } catch (err) {
      alert(`Download failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setDownloading(null);
    }
  };

  const loadVersionDetails = async (versionId: string) => {
    try {
      console.log(`Loading version details for ${versionId}...`);
      const data = await apiClient.get<ExampleVersionGet>(`/examples/versions/${versionId}`);
      console.log(`Loaded version details for ${versionId}:`, data);
      setFullVersionDetails(prev => ({
        ...prev,
        [versionId]: data
      }));
    } catch (err) {
      console.error(`Error loading version ${versionId} details:`, err);
    }
  };

  const loadAllVersionDetails = async () => {
    console.log(`loadAllVersionDetails called. Versions count: ${versions.length}`);
    console.log('Versions:', versions);
    console.log('Already loaded details:', Object.keys(fullVersionDetails));
    
    if (versions.length === 0 || Object.keys(fullVersionDetails).length === versions.length) {
      console.log('Skipping load - already loaded or no versions');
      return; // Already loaded or no versions
    }
    
    setLoadingMetadata(true);
    try {
      console.log('Starting to load version details...');
      await Promise.all(
        versions.map(version => {
          if (!fullVersionDetails[version.id]) {
            console.log(`Loading details for version ${version.id}`);
            return loadVersionDetails(version.id);
          }
          console.log(`Already have details for version ${version.id}`);
          return Promise.resolve();
        })
      );
      console.log('All version details loaded');
    } catch (error) {
      console.error('Error loading version details:', error);
    } finally {
      setLoadingMetadata(false);
    }
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) {
      return '—';
    }
    
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return '—';
    }
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const parseMetaYaml = (metaYaml: string) => {
    try {
      return yaml.load(metaYaml) as any;
    } catch (err) {
      return null;
    }
  };

  const parseTestYaml = (testYaml: string) => {
    try {
      return yaml.load(testYaml) as any;
    } catch (err) {
      return null;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !example) {
    return (
      <Box>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/admin/examples')}
          sx={{ mb: 2 }}
        >
          Back to Examples
        </Button>
        <Alert severity="error">
          {error || 'Example not found'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/admin/examples')}
          sx={{ mr: 2 }}
        >
          Back to Examples
        </Button>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          {example.title}
        </Typography>
      </Box>

      {/* Example Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Typography variant="h6" gutterBottom>
                <CodeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Example Information
              </Typography>
              <Typography variant="body1" paragraph>
                <strong>Directory:</strong> {example.directory}
              </Typography>
              <Typography variant="body1" paragraph>
                <strong>Identifier:</strong> {example.identifier}
              </Typography>
              {example.description && (
                <Typography variant="body1" paragraph>
                  <strong>Description:</strong> {example.description}
                </Typography>
              )}
              <Typography variant="body1" paragraph>
                <strong>Subject:</strong> {example.subject || 'Not specified'}
              </Typography>
              {example.tags && example.tags.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Tags:</strong>
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {example.tags.map((tag, index) => (
                      <Chip key={index} label={tag} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Box>
              )}
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                <StorageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Repository
              </Typography>
              {example.repository && (
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>{example.repository.name}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {example.repository.description}
                  </Typography>
                  <Chip 
                    label={example.repository.source_type?.toUpperCase() || 'UNKNOWN'} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                    sx={{ mt: 1 }}
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {example.repository.source_url}
                  </Typography>
                </Paper>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>


      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label={`Versions (${versions.length})`} />
          <Tab label="Dependencies" />
        </Tabs>
      </Box>

      {/* Versions Tab */}
      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" gutterBottom>
          <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Version History
        </Typography>
        
        {versions.length === 0 ? (
          <Alert severity="info">No versions found for this example.</Alert>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Version</TableCell>
                  <TableCell>Tag</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {versions.map((version) => (
                  <TableRow 
                    key={version.id}
                    hover
                    selected={selectedVersionId === version.id}
                    onClick={() => setSelectedVersionId(version.id)}
                    sx={{ 
                      cursor: 'pointer',
                      '&.Mui-selected': {
                        backgroundColor: 'action.selected',
                      },
                      '&.Mui-selected:hover': {
                        backgroundColor: 'action.selected',
                      }
                    }}
                  >
                    <TableCell>
                      <Chip 
                        label={`v${version.version_number}`} 
                        size="small" 
                        color={selectedVersionId === version.id ? "primary" : "default"}
                        variant={selectedVersionId === version.id ? "filled" : "outlined"}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: selectedVersionId === version.id ? 'medium' : 'normal'
                        }}
                      >
                        {version.version_tag}
                      </Typography>
                    </TableCell>
                    <TableCell>{formatDate(version.created_at)}</TableCell>
                    <TableCell>
                      <Tooltip title="Download Version">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation(); // Prevent row selection when clicking download
                            handleDownload(version.id, version.version_tag);
                          }}
                          disabled={downloading === version.id}
                        >
                          {downloading === version.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <CloudDownloadIcon />
                          )}
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </TabPanel>

      {/* Dependencies Tab */}
      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          Dependencies
        </Typography>
        {example.dependencies && example.dependencies.length > 0 ? (
          <Paper variant="outlined" sx={{ p: 2 }}>
            {example.dependencies.map((dep) => (
              <Typography key={dep.id} variant="body2">
                • Depends on: {dep.depends_id}
              </Typography>
            ))}
          </Paper>
        ) : (
          <Alert severity="info">This example has no dependencies.</Alert>
        )}
      </TabPanel>

      {/* Version Metadata Section - Below Tabs */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              Version Metadata
            </Typography>
            
            {/* Version Selector */}
            {versions.length > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Select Version:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {versions.map((version) => (
                    <Chip
                      key={version.id}
                      label={version.version_tag}
                      variant={selectedVersionId === version.id ? "filled" : "outlined"}
                      color={selectedVersionId === version.id ? "primary" : "default"}
                      clickable
                      onClick={() => setSelectedVersionId(version.id)}
                      size="small"
                    />
                  ))}
                </Box>
              </Box>
            )}
          </Box>
          
          {versions.length === 0 ? (
            <Alert severity="info">No versions available.</Alert>
          ) : !selectedVersionId ? (
            <Alert severity="info">Select a version to view metadata.</Alert>
          ) : (() => {
            const selectedVersion = versions.find(v => v.id === selectedVersionId);
            const fullVersion = fullVersionDetails[selectedVersionId];
            const hasFullData = fullVersion && fullVersion.meta_yaml !== undefined;
            
            if (!selectedVersion) {
              return <Alert severity="error">Selected version not found.</Alert>;
            }
            
            return (
              <Box>
                <Typography variant="subtitle1" gutterBottom sx={{ mb: 2 }}>
                  {selectedVersion.version_tag} ({formatDate(selectedVersion.created_at)})
                </Typography>
                
                {!hasFullData ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <CircularProgress size={24} />
                    <Typography variant="body2" sx={{ ml: 2 }}>
                      Loading metadata...
                    </Typography>
                  </Box>
                ) : (
                  <Grid container spacing={3}>
                    {fullVersion.meta_yaml ? (
                      <Grid item xs={12} md={fullVersion.test_yaml ? 6 : 12}>
                        <Typography variant="subtitle2" gutterBottom>
                          meta.yaml
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
                          <pre style={{ fontSize: '0.8rem', margin: 0, whiteSpace: 'pre-wrap' }}>
                            {fullVersion.meta_yaml}
                          </pre>
                        </Paper>
                      </Grid>
                    ) : (
                      <Grid item xs={12}>
                        <Alert severity="warning">No meta.yaml found for this version.</Alert>
                      </Grid>
                    )}
                    {fullVersion.test_yaml && (
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" gutterBottom>
                          test.yaml
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
                          <pre style={{ fontSize: '0.8rem', margin: 0, whiteSpace: 'pre-wrap' }}>
                            {fullVersion.test_yaml}
                          </pre>
                        </Paper>
                      </Grid>
                    )}
                    {fullVersion.storage_path && (
                      <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">
                          Storage Path: {fullVersion.storage_path}
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                )}
              </Box>
            );
          })()}
        </CardContent>
      </Card>
    </Box>
  );
};

export default ExampleDetailPage;