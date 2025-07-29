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
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';

import { DataTable, Column } from './common/DataTable';
import { Example, ExampleRepository, ExampleDownloadResponse } from '../types/examples';
import { apiClient } from '../services/apiClient';

interface ExamplesTableProps {
  data: Example[];
  repositories: ExampleRepository[];
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
  const [selectedExample, setSelectedExample] = useState<Example | null>(null);

  // Filter data based on search
  const filteredData = data.filter(example =>
    example.title.toLowerCase().includes(searchValue.toLowerCase()) ||
    example.identifier.toLowerCase().includes(searchValue.toLowerCase()) ||
    example.directory.toLowerCase().includes(searchValue.toLowerCase()) ||
    (example.subject && example.subject.toLowerCase().includes(searchValue.toLowerCase())) ||
    (example.category && example.category.toLowerCase().includes(searchValue.toLowerCase())) ||
    example.tags.some(tag => tag.toLowerCase().includes(searchValue.toLowerCase()))
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

  const handleActionClick = (event: React.MouseEvent<HTMLElement>, example: Example) => {
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
        // First, get the full example details with versions
        const fullExample = await apiClient.get<Example>(`/examples/${selectedExample.id}`);
        
        if (!fullExample.versions || fullExample.versions.length === 0) {
          alert('No versions available for download');
          handleActionClose();
          return;
        }
        
        // Download the latest version
        const latestVersion = fullExample.versions[0];
        const response = await apiClient.get<ExampleDownloadResponse>(`/examples/download/${latestVersion.id}`);
        
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
        link.download = `${selectedExample.directory}-${latestVersion.version_tag}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        URL.revokeObjectURL(downloadUrl);
        
      } catch (err) {
        alert(`Download failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    }
    handleActionClose();
  };


  const handleViewDetails = () => {
    if (selectedExample) {
      navigate(`/admin/examples/${selectedExample.id}`);
    }
    handleActionClose();
  };

  const columns: Column<Example>[] = [
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
          {example.tags.slice(0, 3).map((tag, index) => (
            <Chip
              key={index}
              label={tag}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.75rem' }}
            />
          ))}
          {example.tags.length > 3 && (
            <Chip
              label={`+${example.tags.length - 3}`}
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
      render: (_, example) => (
        <Typography variant="body2">
          {new Date(example.updated_at).toLocaleDateString()}
        </Typography>
      ),
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
    </>
  );
};

export default ExamplesTable;