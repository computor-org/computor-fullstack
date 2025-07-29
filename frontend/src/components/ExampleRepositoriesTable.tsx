import React, { useState } from 'react';
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
  Sync as SyncIcon,
  Storage as StorageIcon,
  GitHub as GitHubIcon,
  Cloud as CloudIcon,
} from '@mui/icons-material';

import { DataTable, Column } from './common/DataTable';
import { ExampleRepository } from '../types/examples';

interface ExampleRepositoriesTableProps {
  data: ExampleRepository[];
  loading?: boolean;
  onEdit: (repository: ExampleRepository) => void;
  onDelete: (repositoryId: string) => void;
  onRefresh?: () => void;
}

const ExampleRepositoriesTable: React.FC<ExampleRepositoriesTableProps> = ({
  data,
  loading = false,
  onEdit,
  onDelete,
  onRefresh,
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchValue, setSearchValue] = useState('');
  const [actionMenuAnchor, setActionMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedRepository, setSelectedRepository] = useState<ExampleRepository | null>(null);

  // Filter data based on search
  const filteredData = data.filter(repository =>
    repository.name.toLowerCase().includes(searchValue.toLowerCase()) ||
    repository.source_type.toLowerCase().includes(searchValue.toLowerCase()) ||
    repository.source_url.toLowerCase().includes(searchValue.toLowerCase()) ||
    (repository.description && repository.description.toLowerCase().includes(searchValue.toLowerCase()))
  );

  // Get paginated data
  const paginatedData = filteredData.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const getSourceTypeIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'git':
      case 'github':
      case 'gitlab':
        return <GitHubIcon fontSize="small" />;
      case 'minio':
      case 's3':
        return <CloudIcon fontSize="small" />;
      default:
        return <StorageIcon fontSize="small" />;
    }
  };

  const getSourceTypeColor = (sourceType: string): 'primary' | 'secondary' | 'success' | 'warning' => {
    switch (sourceType) {
      case 'git':
        return 'primary';
      case 'github':
        return 'secondary';
      case 'gitlab':
        return 'warning';
      case 'minio':
      case 's3':
        return 'success';
      default:
        return 'primary';
    }
  };

  const handleActionClick = (event: React.MouseEvent<HTMLElement>, repository: ExampleRepository) => {
    setActionMenuAnchor(event.currentTarget);
    setSelectedRepository(repository);
  };

  const handleActionClose = () => {
    setActionMenuAnchor(null);
    setSelectedRepository(null);
  };

  const handleEdit = () => {
    if (selectedRepository) {
      onEdit(selectedRepository);
    }
    handleActionClose();
  };

  const handleDelete = () => {
    if (selectedRepository) {
      onDelete(selectedRepository.id);
    }
    handleActionClose();
  };

  const handleSync = () => {
    if (selectedRepository) {
      // TODO: Implement sync functionality
      console.log('Sync repository:', selectedRepository.id);
    }
    handleActionClose();
  };

  const columns: Column<ExampleRepository>[] = [
    {
      id: 'name',
      label: 'Name',
      render: (_, repository) => (
        <Box>
          <Typography variant="subtitle2">{repository.name}</Typography>
          {repository.description && (
            <Typography variant="caption" color="text.secondary">
              {repository.description}
            </Typography>
          )}
        </Box>
      ),
    },
    {
      id: 'source_type',
      label: 'Source Type',
      render: (_, repository) => (
        <Chip
          icon={getSourceTypeIcon(repository.source_type)}
          label={repository.source_type.toUpperCase()}
          color={getSourceTypeColor(repository.source_type)}
          variant="outlined"
          size="small"
        />
      ),
    },
    {
      id: 'source_url',
      label: 'Source URL',
      render: (_, repository) => (
        <Box sx={{ maxWidth: 300 }}>
          <Typography 
            variant="body2" 
            sx={{ 
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              wordBreak: 'break-all',
            }}
          >
            {repository.source_url}
          </Typography>
        </Box>
      ),
    },
    {
      id: 'default_version',
      label: 'Default Version',
      render: (_, repository) => (
        repository.default_version ? (
          <Chip 
            label={repository.default_version} 
            variant="outlined" 
            size="small"
            sx={{ fontFamily: 'monospace' }}
          />
        ) : (
          <Typography variant="body2" color="text.secondary">—</Typography>
        )
      ),
    },
    {
      id: 'credentials',
      label: 'Credentials',
      align: 'center',
      render: (_, repository) => (
        <Chip
          label={repository.access_credentials ? 'Yes' : 'No'}
          color={repository.access_credentials ? 'success' : 'default'}
          variant="outlined"
          size="small"
        />
      ),
    },
    {
      id: 'updated_at',
      label: 'Last Updated',
      render: (_, repository) => (
        <Typography variant="body2">
          {new Date(repository.updated_at).toLocaleDateString()}
        </Typography>
      ),
    },
    {
      id: 'actions',
      label: 'Actions',
      align: 'center',
      render: (_, repository) => (
        <IconButton
          size="small"
          onClick={(e) => handleActionClick(e, repository)}
        >
          <MoreIcon />
        </IconButton>
      ),
    },
  ];

  return (
    <>
      <DataTable
        title="Example Repositories"
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
        emptyMessage="No repositories found. Add a repository to get started."
      />

      {/* Actions Menu */}
      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={handleActionClose}
      >
        <MenuItem onClick={handleEdit}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleSync}>
          <ListItemIcon>
            <SyncIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Sync Repository</ListItemText>
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

export default ExampleRepositoriesTable;