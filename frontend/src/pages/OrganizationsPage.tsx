import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  Stack,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Business as BusinessIcon,
  Group as GroupIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useQueryClient } from '@tanstack/react-query';
import { OrganizationGet, OrganizationUpdate } from '../types/generated/organizations';
import { DataTable, Column } from '../components/common/DataTable';
import { FormDialog } from '../components/common/FormDialog';
import OrganizationForm from '../components/OrganizationForm';
import DeleteDialog from '../components/DeleteDialog';
import { useOrganizationListQuery, organizationKeys } from '../app/queries/organizationQueries';
import { organizationService } from '../services/organizationService';

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

const OrganizationsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchValue, setSearchValue] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<OrganizationGet | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchTerm(searchValue);
      setPage(0);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchValue]);

  const queryParams = useMemo(
    () => ({
      limit: rowsPerPage,
      offset: page * rowsPerPage,
      title: searchTerm || undefined,
    }),
    [rowsPerPage, page, searchTerm]
  );

  const organizationListQuery = useOrganizationListQuery(queryParams);
  const { data, isLoading, isFetching, error } = organizationListQuery;

  const organizations = data?.items ?? [];
  const totalCount = data?.total ?? 0;
  const errorMessage = error instanceof Error ? error.message : null;

  const handleCreate = () => {
    navigate('/admin/organizations/create');
  };

  const handleEdit = (org: OrganizationGet) => {
    setSelectedOrg(org);
    setFormOpen(true);
  };

  const handleDelete = (org: OrganizationGet) => {
    setSelectedOrg(org);
    setDeleteOpen(true);
  };

  const [formError, setFormError] = useState<string | null>(null);

  const handleFormSubmit = async (data: OrganizationUpdate) => {
    if (!selectedOrg) return;

    try {
      setFormLoading(true);
      setFormError(null);
      await organizationService.updateOrganization(selectedOrg.id, data);
      setFormOpen(false);
      setSelectedOrg(null);
      await queryClient.invalidateQueries({ queryKey: organizationKeys.all });
    } catch (err: any) {
      console.error('Error saving organization:', err);
      setFormError(err?.message || 'Failed to save organization');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedOrg) return;

    try {
      setDeleteLoading(true);
      await organizationService.deleteOrganization(selectedOrg.id);
      setDeleteOpen(false);
      setSelectedOrg(null);
      await queryClient.invalidateQueries({ queryKey: organizationKeys.all });
    } catch (err: any) {
      console.error('Error deleting organization:', err);
      alert(err.message || 'Failed to delete organization');
    } finally {
      setDeleteLoading(false);
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
        <Chip icon={getOrgTypeIcon(value)} label={value} size="small" variant="outlined" />
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
        Organizations
      </Typography>

      <DataTable
        title="Organizations"
        columns={columns}
        data={organizations}
        loading={isLoading || isFetching}
        error={errorMessage}
        totalCount={totalCount}
        page={page}
        rowsPerPage={rowsPerPage}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        onPageChange={setPage}
        onRowsPerPageChange={(value) => {
          setRowsPerPage(value);
          setPage(0);
        }}
        onRefresh={() => organizationListQuery.refetch()}
        onRowClick={(org) => navigate(`/admin/organizations/${org.id}`)}
        rowActions={rowActions}
        actions={
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
            Create Organization
          </Button>
        }
      />

      <FormDialog
        open={formOpen}
        title="Edit Organization"
        onClose={() => {
          setFormOpen(false);
          setSelectedOrg(null);
          setFormError(null);
        }}
        loading={formLoading}
      >
        <OrganizationForm
          organization={selectedOrg}
          mode="edit"
          onSubmit={handleFormSubmit}
          onClose={() => {
            setFormOpen(false);
            setSelectedOrg(null);
            setFormError(null);
          }}
          loading={formLoading}
          error={formError}
        />
      </FormDialog>

      <DeleteDialog
        open={deleteOpen}
        title="Delete Organization"
        message={`Are you sure you want to delete ${selectedOrg?.title || 'this organization'}?`}
        onClose={() => {
          setDeleteOpen(false);
          setSelectedOrg(null);
        }}
        onConfirm={handleDeleteConfirm}
        loading={deleteLoading}
      />
    </Box>
  );
};

export default OrganizationsPage;
