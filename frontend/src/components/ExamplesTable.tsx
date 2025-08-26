import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Chip,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControlLabel,
  Checkbox,
  Alert,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';

import { DataTable, Column } from './common/DataTable';
import { ExampleList, ExampleRepositoryGet, ExampleDownloadResponse, ExampleGet } from '../types/generated/examples';
import { apiClient } from '../services/apiClient';

interface ExamplesTableProps {
  data: ExampleList[];
  repositories: ExampleRepositoryGet[];
  loading?: boolean;
  onDelete: (exampleId: string) => void;
  onRefresh?: () => void;
}

const ExamplesTable: React.FC<ExamplesTableProps> = ({
  data,
  repositories,
  loading = false,
  onDelete,
  onRefresh,
}) => {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchValue, setSearchValue] = useState('');
  const [actionMenuAnchor, setActionMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedExample, setSelectedExample] = useState<ExampleList | null>(null);
  const [downloadDialogOpen, setDownloadDialogOpen] = useState(false);
  const [includeDependencies, setIncludeDependencies] = useState(false);
  const [exampleHasDependencies, setExampleHasDependencies] = useState(false);

  // Filter data based on search
  const filteredData = data.filter(example =>
    example.title.toLowerCase().includes(searchValue.toLowerCase()) ||
    example.identifier.toLowerCase().includes(searchValue.toLowerCase()) ||
    example.directory.toLowerCase().includes(searchValue.toLowerCase()) ||
    (example.subject && example.subject.toLowerCase().includes(searchValue.toLowerCase())) ||
    (example.category && example.category.toLowerCase().includes(searchValue.toLowerCase())) ||
    (example.tags && example.tags.some(tag => tag.toLowerCase().includes(searchValue.toLowerCase())))
  );

  // Get paginated data
  const paginatedData = filteredData.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const getRepositoryName = (repositoryId: string) => {
    const repo = repositories.find(r => r.id === repositoryId);
    return repo?.name || 'Unknown Repository';
  };

  const handleActionClick = (event: React.MouseEvent<HTMLElement>, example: ExampleList) => {
    setActionMenuAnchor(event.currentTarget);
    setSelectedExample(example);
  };

  const handleActionClose = () => {
    setActionMenuAnchor(null);
    setSelectedExample(null);
  };


  const handleDelete = () => {
    if (selectedExample) {
      onDelete(selectedExample.id);
    }
    handleActionClose();
  };

  const handleDownload = async () => {
    if (selectedExample) {
      try {
        // First, get the full example details with versions and dependencies
        const fullExample = await apiClient.get<ExampleGet>(`/examples/${selectedExample.id}`);
        
        if (!fullExample.versions || fullExample.versions.length === 0) {
          alert('No versions available for download');
          handleActionClose();
          return;
        }
        
        // Check if example has dependencies
        const hasDependencies = !!(fullExample.dependencies && fullExample.dependencies.length > 0);
        setExampleHasDependencies(hasDependencies);
        
        if (hasDependencies) {
          // Show dialog to ask about including dependencies
          setDownloadDialogOpen(true);
        } else {
          // Proceed with direct download
          await performDownload(false);
        }
        
      } catch (err) {
        alert(`Download failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
        handleActionClose();
      }
    }
  };

  const performDownload = async (withDependencies: boolean) => {
    if (!selectedExample) return;
    
    try {
      // Get the full example details again
      const fullExample = await apiClient.get<ExampleGet>(`/examples/${selectedExample.id}`);
      const latestVersion = fullExample.versions![0];
      
      // Download with or without dependencies
      const apiUrl = `/examples/download/${latestVersion.id}${withDependencies ? '?with_dependencies=true' : ''}`;
      const response = await apiClient.get<ExampleDownloadResponse>(apiUrl);
      
      // Create a ZIP file with all the example files
      const JSZip = require('jszip');
      const zip = new JSZip();
      
      // Add main example files to the ZIP (using its identifier as directory name)
      const mainExampleFolder = fullExample.identifier;
      for (const [filename, content] of Object.entries(response.files)) {
        zip.file(`${mainExampleFolder}/${filename}`, content);
      }
      
      // Add meta.yaml and test.yaml if they exist
      if (response.meta_yaml) {
        zip.file(`${mainExampleFolder}/meta.yaml`, response.meta_yaml);
      }
      if (response.test_yaml) {
        zip.file(`${mainExampleFolder}/test.yaml`, response.test_yaml);
      }
      
      // Add dependencies if included (each as separate directory with identifier name)
      if (withDependencies && response.dependencies) {
        for (const dep of response.dependencies) {
          const depFolder = dep.identifier; // Use identifier as directory name
          
          // Add dependency files
          for (const [filename, content] of Object.entries(dep.files)) {
            zip.file(`${depFolder}/${filename}`, content);
          }
          
          // Add dependency meta.yaml and test.yaml
          if (dep.meta_yaml) {
            zip.file(`${depFolder}/meta.yaml`, dep.meta_yaml);
          }
          if (dep.test_yaml) {
            zip.file(`${depFolder}/test.yaml`, dep.test_yaml);
          }
        }
      }
      
      // Generate and download the ZIP
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      const downloadUrl = URL.createObjectURL(zipBlob);
      
      // Create temporary download link
      const link = document.createElement('a');
      link.href = downloadUrl;
      const suffix = withDependencies ? '-with-dependencies' : '';
      link.download = `${selectedExample.directory}-${latestVersion.version_tag}${suffix}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up
      URL.revokeObjectURL(downloadUrl);
      
    } catch (err) {
      alert(`Download failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
    
    setDownloadDialogOpen(false);
    handleActionClose();
  };


  const handleViewDetails = () => {
    if (selectedExample) {
      navigate(`/admin/examples/${selectedExample.id}`);
    }
    handleActionClose();
  };

  const columns: Column<ExampleList>[] = [
    {
      id: 'title',
      label: 'Title',
      render: (_, example) => (
        <Box>
          <Typography variant="subtitle2">{example.title}</Typography>
          <Typography variant="caption" color="text.secondary">
            {example.identifier}
          </Typography>
        </Box>
      ),
    },
    {
      id: 'directory',
      label: 'Directory',
      accessor: (example) => example.directory,
      render: (value) => (
        <Chip 
          label={value} 
          variant="outlined" 
          size="small"
          sx={{ fontFamily: 'monospace' }}
        />
      ),
    },
    {
      id: 'repository',
      label: 'Repository',
      render: (_, example) => (
        <Typography variant="body2">
          {getRepositoryName(example.example_repository_id)}
        </Typography>
      ),
    },
    {
      id: 'subject',
      label: 'Subject',
      render: (_, example) => (
        example.subject ? (
          <Chip 
            label={example.subject} 
            color="primary" 
            variant="outlined" 
            size="small"
          />
        ) : (
          <Typography variant="body2" color="text.secondary">—</Typography>
        )
      ),
    },
    {
      id: 'category',
      label: 'Category',
      render: (_, example) => (
        example.category ? (
          <Chip 
            label={example.category} 
            color="secondary" 
            variant="outlined" 
            size="small"
          />
        ) : (
          <Typography variant="body2" color="text.secondary">—</Typography>
        )
      ),
    },
    {
      id: 'tags',
      label: 'Tags',
      render: (_, example) => (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxWidth: 200 }}>
          {(example.tags || []).slice(0, 3).map((tag, index) => (
            <Chip
              key={index}
              label={tag}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.75rem' }}
            />
          ))}
          {(example.tags || []).length > 3 && (
            <Chip
              label={`+${(example.tags || []).length - 3}`}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.75rem' }}
            />
          )}
        </Box>
      ),
    },
    {
      id: 'updated_at',
      label: 'Last Updated',
      render: (_, example) => {
        // Handle missing or invalid dates
        if (!example.updated_at) {
          return <Typography variant="body2" color="text.secondary">—</Typography>;
        }
        
        const date = new Date(example.updated_at);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
          return <Typography variant="body2" color="text.secondary">—</Typography>;
        }
        
        return (
          <Typography variant="body2">
            {date.toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            })}
          </Typography>
        );
      },
    },
    {
      id: 'actions',
      label: 'Actions',
      align: 'center',
      render: (_, example) => (
        <IconButton
          size="small"
          onClick={(e) => handleActionClick(e, example)}
        >
          <MoreIcon />
        </IconButton>
      ),
    },
  ];

  return (
    <>
      <DataTable
        title="Examples"
        columns={columns}
        data={paginatedData}
        loading={loading}
        totalCount={filteredData.length}
        page={page}
        rowsPerPage={rowsPerPage}
        searchValue={searchValue}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        onSearchChange={setSearchValue}
        onRefresh={onRefresh}
        emptyMessage="No examples found. Add some examples to get started."
      />

      {/* Actions Menu */}
      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={handleActionClose}
      >
        <MenuItem onClick={handleViewDetails}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleDownload}>
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Download Dependencies Dialog */}
      <Dialog open={downloadDialogOpen} onClose={() => setDownloadDialogOpen(false)}>
        <DialogTitle>Download Options</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            This example has dependencies. You can choose to download them along with the main example.
          </Alert>
          <FormControlLabel
            control={
              <Checkbox
                checked={includeDependencies}
                onChange={(e) => setIncludeDependencies(e.target.checked)}
              />
            }
            label="Include dependencies"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDownloadDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => performDownload(includeDependencies)}
            variant="contained"
            color="primary"
          >
            Download
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ExamplesTable;