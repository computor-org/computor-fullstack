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

import { Example, ExampleRepository, ExampleDownloadResponse } from '../types/examples';
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

interface ExampleVersion {
  id: string;
  version_tag: string;
  version_number: number;
  created_at: string;
  meta_yaml?: string;
  test_yaml?: string;
}

const ExampleDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [example, setExample] = useState<Example | null>(null);
  const [versions, setVersions] = useState<ExampleVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadExampleDetail();
      loadVersions();
    }
  }, [id]);

  const loadExampleDetail = async () => {
    try {
      const data = await apiClient.get<Example>(`/examples/${id}`);
      setExample(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load example');
    }
  };

  const loadVersions = async () => {
    try {
      const data = await apiClient.get<ExampleVersion[]>(`/examples/${id}/versions`);
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

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
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
          onClick={() => navigate('/examples')}
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
          onClick={() => navigate('/examples')}
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
                    label={example.repository.source_type.toUpperCase()} 
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
          <Tab label="Metadata" />
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
                  <TableRow key={version.id}>
                    <TableCell>
                      <Chip 
                        label={`v${version.version_number}`} 
                        size="small" 
                        color="primary"
                      />
                    </TableCell>
                    <TableCell>{version.version_tag}</TableCell>
                    <TableCell>{formatDate(version.created_at)}</TableCell>
                    <TableCell>
                      <Tooltip title="Download Version">
                        <IconButton
                          size="small"
                          onClick={() => handleDownload(version.id, version.version_tag)}
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

      {/* Metadata Tab */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" gutterBottom>
          Version Metadata
        </Typography>
        
        {versions.map((version) => {
          const metaData = version.meta_yaml ? parseMetaYaml(version.meta_yaml) : null;
          const testData = version.test_yaml ? parseTestYaml(version.test_yaml) : null;
          
          return (
            <Accordion key={version.id}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>
                  Version {version.version_tag} - Metadata
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {metaData && (
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        meta.yaml
                      </Typography>
                      <Paper variant="outlined" sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
                        <pre style={{ fontSize: '0.8rem', margin: 0 }}>
                          {version.meta_yaml}
                        </pre>
                      </Paper>
                    </Grid>
                  )}
                  {testData && (
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        test.yaml
                      </Typography>
                      <Paper variant="outlined" sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
                        <pre style={{ fontSize: '0.8rem', margin: 0 }}>
                          {version.test_yaml}
                        </pre>
                      </Paper>
                    </Grid>
                  )}
                </Grid>
              </AccordionDetails>
            </Accordion>
          );
        })}
        
        {versions.length === 0 && (
          <Alert severity="info">No metadata available.</Alert>
        )}
      </TabPanel>
    </Box>
  );
};

export default ExampleDetailPage;