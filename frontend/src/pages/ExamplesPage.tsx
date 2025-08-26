import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  Tabs,
  Tab,
  Card,
  CardContent,
  Chip,
  Grid,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

import ExamplesTable from '../components/ExamplesTable';
import ExampleRepositoriesTable from '../components/ExampleRepositoriesTable';
import ExampleRepositoryForm from '../components/ExampleRepositoryForm';
import ExampleUploadDialog from '../components/ExampleUploadDialog';
import { ExampleList, ExampleRepositoryGet, ExampleRepositoryCreate } from '../types/generated/examples';
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
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const ExamplesPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  
  // Examples state
  const [examples, setExamples] = useState<ExampleList[]>([]);
  
  // Repositories state
  const [repositories, setRepositories] = useState<ExampleRepositoryGet[]>([]);
  const [isRepositoryFormOpen, setIsRepositoryFormOpen] = useState(false);
  const [editingRepository, setEditingRepository] = useState<ExampleRepositoryGet | null>(null);
  
  // Upload state
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  
  // Loading and error states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stats
  const [stats, setStats] = useState({
    totalExamples: 0,
    totalRepositories: 0,
    totalVersions: 0,
    recentUploads: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  // Update stats whenever examples or repositories change
  useEffect(() => {
    loadStats();
  }, [examples, repositories]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      await loadExamples();
      await loadRepositories();
      // loadStats() will be called automatically when examples/repositories change
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadExamples = async () => {
    try {
      const data = await apiClient.get<ExampleList[]>('/examples');
      setExamples(data);
    } catch (err) {
      console.error('Error fetching examples:', err);
      setExamples([]);
    }
  };

  const loadRepositories = async () => {
    try {
      const data = await apiClient.get<ExampleRepositoryGet[]>('/example-repositories');
      setRepositories(data);
    } catch (err) {
      console.error('Error fetching repositories:', err);
      setRepositories([]);
    }
  };

  const loadStats = async () => {
    // Calculate stats from loaded data
    setStats({
      totalExamples: examples.length,
      totalRepositories: repositories.length,
      totalVersions: 0, // Version count not available in list view
      recentUploads: examples.filter(e => {
        if (!e.created_at) return false;
        const createdAt = new Date(e.created_at);
        const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
        return createdAt > dayAgo;
      }).length,
    });
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Example handlers
  const handleDeleteExample = async (exampleId: string) => {
    if (window.confirm('Are you sure you want to delete this example?')) {
      try {
        // TODO: Implement API call
        // await apiClient.delete(`/examples/${exampleId}`);
        setExamples(examples.filter(e => e.id !== exampleId));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete example');
      }
    }
  };

  // Repository handlers
  const handleAddRepository = () => {
    setEditingRepository(null);
    setIsRepositoryFormOpen(true);
  };

  const handleEditRepository = (repository: ExampleRepositoryGet) => {
    setEditingRepository(repository);
    setIsRepositoryFormOpen(true);
  };

  const handleDeleteRepository = async (repositoryId: string) => {
    if (window.confirm('Are you sure you want to delete this repository? This will also delete all associated examples.')) {
      try {
        // TODO: Implement API call
        // await apiClient.delete(`/example-repositories/${repositoryId}`);
        setRepositories(repositories.filter(r => r.id !== repositoryId));
        setExamples(examples.filter(e => e.example_repository_id !== repositoryId));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete repository');
      }
    }
  };

  const handleSaveRepository = async (repositoryData: ExampleRepositoryCreate) => {
    try {
      if (editingRepository) {
        // TODO: Implement API call
        // await apiClient.put(`/example-repositories/${editingRepository.id}`, repositoryData);
        setRepositories(repositories.map(r => 
          r.id === editingRepository.id 
            ? { ...repositoryData, id: editingRepository.id, created_at: editingRepository.created_at, updated_at: new Date().toISOString() }
            : r
        ));
      } else {
        // TODO: Implement API call
        // const response = await apiClient.post('/example-repositories', repositoryData);
        const newRepository: ExampleRepositoryGet = {
          ...repositoryData,
          id: Date.now().toString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setRepositories([...repositories, newRepository]);
      }
      setIsRepositoryFormOpen(false);
      setEditingRepository(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save repository');
    }
  };

  const handleUploadSuccess = () => {
    setIsUploadDialogOpen(false);
    loadData(); // Refresh data after upload
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Example Library
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => setIsUploadDialogOpen(true)}
          >
            Upload Example Directory
          </Button>
          {tabValue === 1 && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddRepository}
            >
              Add Repository
            </Button>
          )}
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CodeIcon color="primary" />
              <Box>
                <Typography variant="h6">{stats.totalExamples}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Examples
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <StorageIcon color="secondary" />
              <Box>
                <Typography variant="h6">{stats.totalRepositories}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Repositories
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <DownloadIcon color="success" />
              <Box>
                <Typography variant="h6">{stats.totalVersions}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Versions
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <UploadIcon color="info" />
              <Box>
                <Typography variant="h6">{stats.recentUploads}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Recent Uploads
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Examples" />
          <Tab label="Repositories" />
        </Tabs>
      </Box>

      {/* Examples Tab */}
      <TabPanel value={tabValue} index={0}>
        <ExamplesTable
          data={examples}
          repositories={repositories}
          loading={loading}
          onDelete={handleDeleteExample}
          onRefresh={loadExamples}
        />
      </TabPanel>

      {/* Repositories Tab */}
      <TabPanel value={tabValue} index={1}>
        <ExampleRepositoriesTable
          data={repositories}
          loading={loading}
          onEdit={handleEditRepository}
          onDelete={handleDeleteRepository}
          onRefresh={loadRepositories}
        />
      </TabPanel>


      {/* Repository Form Dialog */}
      <Dialog
        open={isRepositoryFormOpen}
        onClose={() => setIsRepositoryFormOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <ExampleRepositoryForm
          repository={editingRepository}
          onSave={handleSaveRepository}
          onCancel={() => setIsRepositoryFormOpen(false)}
        />
      </Dialog>

      {/* Upload Dialog */}
      <ExampleUploadDialog
        open={isUploadDialogOpen}
        repositories={repositories}
        onClose={() => setIsUploadDialogOpen(false)}
        onSuccess={handleUploadSuccess}
      />
    </Box>
  );
};

export default ExamplesPage;