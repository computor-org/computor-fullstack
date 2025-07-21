import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Alert,
  Chip,
} from '@mui/material';
import {
  Security as SecurityIcon,
} from '@mui/icons-material';
import { RoleGet } from '../types/generated/roles';
import { apiClient } from '../services/apiClient';
import { DataTable, Column } from '../components/common/DataTable';

const RolesPage: React.FC = () => {
  const [roles, setRoles] = useState<RoleGet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);

  // Load roles
  const loadRoles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.get<any>('/roles', {
        params: {
          limit: rowsPerPage,
          offset: page * rowsPerPage,
        },
      });

      const total = response.headers?.['x-total-count'] || response.data?.length || 0;
      const data = Array.isArray(response) ? response : response.data || [];

      setRoles(data);
      setTotalCount(parseInt(total, 10));
    } catch (err: any) {
      console.error('Error loading roles:', err);
      setError(err.message || 'Failed to load roles');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage]);

  useEffect(() => {
    loadRoles();
  }, [loadRoles]);

  const columns: Column<RoleGet>[] = [
    {
      id: 'title',
      label: 'Role',
      render: (value, row) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SecurityIcon color="action" fontSize="small" />
          <Typography variant="subtitle2">
            {value || `Role ${row.id.substring(0, 8)}`}
          </Typography>
          {row.builtin && (
            <Chip label="Built-in" size="small" variant="outlined" />
          )}
        </Box>
      ),
    },
    {
      id: 'description',
      label: 'Description',
      render: (value) => (
        <Typography variant="body2" color="text.secondary">
          {value || 'No description available'}
        </Typography>
      ),
    },
    {
      id: 'id',
      label: 'Role ID',
      render: (value) => (
        <Typography variant="caption" fontFamily="monospace">
          {value}
        </Typography>
      ),
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Roles & Permissions
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        Roles are managed by the system. Built-in roles cannot be modified or deleted.
        User role assignments can be managed from the user detail pages.
      </Alert>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <DataTable
        title="System Roles"
        columns={columns}
        data={roles}
        loading={loading}
        error={null}
        totalCount={totalCount}
        page={page}
        rowsPerPage={rowsPerPage}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        onRefresh={loadRoles}
        emptyMessage="No roles found"
      />
    </Box>
  );
};

export default RolesPage;