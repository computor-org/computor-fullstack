import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Chip,
  Stack,
  Typography,
  Alert,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Business as BusinessIcon,
  Group as GroupIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { OrganizationGet, OrganizationCreate, OrganizationUpdate } from '../types/generated/organizations';
import { apiClient } from '../services/apiClient';
import { DataTable, Column } from '../components/common/DataTable';
import { FormDialog } from '../components/common/FormDialog';
import OrganizationForm from '../components/OrganizationForm';
import DeleteDialog from '../components/DeleteDialog';

const OrganizationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<OrganizationGet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [searchValue, setSearchValue] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Dialog states
  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<OrganizationGet | null>(null);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [formLoading, setFormLoading] = useState(false);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchTerm(searchValue);
      setPage(0);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchValue]);

  // Load organizations
  const loadOrganizations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.get<any>('/organizations', {
        params: {
          limit: rowsPerPage,
          offset: page * rowsPerPage,
          ...(searchTerm && { title: searchTerm }),
        },
      });

      // Extract data and total from response headers
      const total = response.headers?.['x-total-count'] || response.data?.length || 0;
      const data = Array.isArray(response) ? response : response.data || [];

      setOrganizations(data);
      setTotalCount(parseInt(total, 10));
    } catch (err: any) {
      console.error('Error loading organizations:', err);
      setError(err.message || 'Failed to load organizations');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, searchTerm]);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  const handleCreate = () => {
    setSelectedOrg(null);
    setFormMode('create');
    setFormOpen(true);
  };

  const handleEdit = (org: OrganizationGet) => {
    setSelectedOrg(org);
    setFormMode('edit');
    setFormOpen(true);
  };

  const handleDelete = (org: OrganizationGet) => {
    setSelectedOrg(org);
    setDeleteOpen(true);
  };

  const handleFormSubmit = async (data: OrganizationCreate | OrganizationUpdate) => {
    try {
      setFormLoading(true);
      if (formMode === 'create') {
        await apiClient.post('/organizations', data);
      } else if (selectedOrg) {
        await apiClient.patch(`/organizations/${selectedOrg.id}`, data);
      }
      setFormOpen(false);
      loadOrganizations();
    } catch (err: any) {
      console.error('Error saving organization:', err);
      alert(err.message || 'Failed to save organization');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedOrg) return;

    try {
      await apiClient.delete(`/organizations/${selectedOrg.id}`);
      setDeleteOpen(false);
      loadOrganizations();
    } catch (err: any) {
      console.error('Error deleting organization:', err);
      alert(err.message || 'Failed to delete organization');
    }
  };

  const getOrgTypeIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <PersonIcon fontSize="small" />;
      case 'community':
        return <GroupIcon fontSize="small" />;
      case 'organization':
        return <BusinessIcon fontSize="small" />;
      default:
        return <BusinessIcon fontSize="small" />;
    }
  };

  const columns: Column<OrganizationGet>[] = [
    {
      id: 'title',
      label: 'Organization',
      render: (value, row) => (
        <Box>
          <Typography variant="subtitle2">
            {value || `User Organization (${row.user_id?.substring(0, 8)}...)`}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {row.path}
          </Typography>
        </Box>
      ),
    },
    {
      id: 'organization_type',
      label: 'Type',
      render: (value) => (
        <Chip
          icon={getOrgTypeIcon(value)}
          label={value}
          size="small"
          variant="outlined"
        />
      ),
    },
    {
      id: 'email',
      label: 'Contact',
      render: (value, row) => (
        <Box>
          {value && <Typography variant="body2">{value}</Typography>}
          {row.telephone && (
            <Typography variant="caption" color="text.secondary">
              {row.telephone}
            </Typography>
          )}
        </Box>
      ),
    },
    {
      id: 'locality',
      label: 'Location',
      render: (value, row) => {
        const parts = [value, row.region, row.country].filter(Boolean);
        return parts.length > 0 ? parts.join(', ') : '-';
      },
    },
  ];

  const rowActions = (row: OrganizationGet) => (
    <Stack direction="row" spacing={0.5}>
      <IconButton size="small" onClick={() => handleEdit(row)}>
        <EditIcon fontSize="small" />
      </IconButton>
      <IconButton size="small" onClick={() => handleDelete(row)}>
        <DeleteIcon fontSize="small" />
      </IconButton>
    </Stack>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Organizations Management
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <DataTable
        title="Organizations"
        columns={columns}
        data={organizations}
        loading={loading}
        error={null}
        totalCount={totalCount}
        page={page}
        rowsPerPage={rowsPerPage}
        searchValue={searchValue}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        onSearchChange={setSearchValue}
        onRefresh={loadOrganizations}
        onRowClick={(org) => navigate(`/admin/organizations/${org.id}`)}
        rowActions={rowActions}
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Add Organization
          </Button>
        }
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={formMode === 'create' ? 'Create Organization' : 'Edit Organization'}
        loading={formLoading}
        maxWidth="md"
      >
        <OrganizationForm
          organization={selectedOrg}
          mode={formMode}
          onSubmit={handleFormSubmit}
          onClose={() => setFormOpen(false)}
        />
      </FormDialog>

      <DeleteDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Organization"
        message={`Are you sure you want to delete "${selectedOrg?.title || 'this organization'}"?`}
      />
    </Box>
  );
};

export default OrganizationsPage;