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
  School as SchoolIcon,
} from '@mui/icons-material';
import { CourseFamilyGet, CourseFamilyCreate, CourseFamilyUpdate } from '../types/generated/courses';
import { OrganizationGet } from '../types/generated/organizations';
import { apiClient } from '../services/apiClient';
import { DataTable, Column } from '../components/common/DataTable';
import { FormDialog } from '../components/common/FormDialog';
import CourseFamilyForm from '../components/CourseFamilyForm';
import DeleteDialog from '../components/DeleteDialog';

const CourseFamiliesPage: React.FC = () => {
  const navigate = useNavigate();
  const [courseFamilies, setCourseFamilies] = useState<CourseFamilyGet[]>([]);
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
  const [selectedCourseFamily, setSelectedCourseFamily] = useState<CourseFamilyGet | null>(null);
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

  // Load organizations for dropdown
  const loadOrganizations = async () => {
    try {
      const response = await apiClient.get<any>('/organizations', {
        params: { limit: 100 },
      });
      const data = Array.isArray(response) ? response : response.data || [];
      setOrganizations(data);
    } catch (err) {
      console.error('Error loading organizations:', err);
    }
  };

  // Load course families
  const loadCourseFamilies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.get<any>('/course-families', {
        params: {
          limit: rowsPerPage,
          offset: page * rowsPerPage,
          ...(searchTerm && { title: searchTerm }),
        },
      });

      const total = response.headers?.['x-total-count'] || response.data?.length || 0;
      const data = Array.isArray(response) ? response : response.data || [];

      setCourseFamilies(data);
      setTotalCount(parseInt(total, 10));
    } catch (err: any) {
      console.error('Error loading course families:', err);
      setError(err.message || 'Failed to load course families');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, searchTerm]);

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    loadCourseFamilies();
  }, [loadCourseFamilies]);

  const handleCreate = () => {
    navigate('/admin/course-families/create');
  };

  const handleEdit = (courseFamily: CourseFamilyGet) => {
    setSelectedCourseFamily(courseFamily);
    setFormMode('edit');
    setFormOpen(true);
  };

  const handleDelete = (courseFamily: CourseFamilyGet) => {
    setSelectedCourseFamily(courseFamily);
    setDeleteOpen(true);
  };

  const handleFormSubmit = async (data: CourseFamilyCreate | CourseFamilyUpdate) => {
    try {
      setFormLoading(true);
      if (formMode === 'create') {
        await apiClient.post('/course-families', data);
      } else if (selectedCourseFamily) {
        await apiClient.patch(`/course-families/${selectedCourseFamily.id}`, data);
      }
      setFormOpen(false);
      loadCourseFamilies();
    } catch (err: any) {
      console.error('Error saving course family:', err);
      alert(err.message || 'Failed to save course family');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedCourseFamily) return;

    try {
      await apiClient.delete(`/course-families/${selectedCourseFamily.id}`);
      setDeleteOpen(false);
      loadCourseFamilies();
    } catch (err: any) {
      console.error('Error deleting course family:', err);
      alert(err.message || 'Failed to delete course family');
    }
  };

  const columns: Column<CourseFamilyGet>[] = [
    {
      id: 'title',
      label: 'Course Family',
      render: (value, row) => (
        <Box>
          <Typography variant="subtitle2">
            {value || 'Untitled Course Family'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {row.path}
          </Typography>
        </Box>
      ),
    },
    {
      id: 'organization',
      label: 'Organization',
      accessor: (row) => row.organization?.title || '-',
      render: (value, row) => (
        <Stack direction="row" spacing={1} alignItems="center">
          <SchoolIcon fontSize="small" color="action" />
          <Typography variant="body2">{value}</Typography>
        </Stack>
      ),
    },
    {
      id: 'description',
      label: 'Description',
      render: (value) => (
        <Typography variant="body2" sx={{ 
          maxWidth: 300, 
          overflow: 'hidden', 
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap' 
        }}>
          {value || '-'}
        </Typography>
      ),
    },
  ];

  const rowActions = (row: CourseFamilyGet) => (
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
        Course Families Management
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <DataTable
        title="Course Families"
        columns={columns}
        data={courseFamilies}
        loading={loading}
        error={null}
        totalCount={totalCount}
        page={page}
        rowsPerPage={rowsPerPage}
        searchValue={searchValue}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        onSearchChange={setSearchValue}
        onRefresh={loadCourseFamilies}
        onRowClick={(cf) => navigate(`/admin/course-families/${cf.id}`)}
        rowActions={rowActions}
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Add Course Family
          </Button>
        }
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={formMode === 'create' ? 'Create Course Family' : 'Edit Course Family'}
        loading={formLoading}
        maxWidth="md"
      >
        <CourseFamilyForm
          courseFamily={selectedCourseFamily}
          organizations={organizations}
          mode={formMode}
          onSubmit={handleFormSubmit}
          onClose={() => setFormOpen(false)}
        />
      </FormDialog>

      <DeleteDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Course Family"
        message={`Are you sure you want to delete "${selectedCourseFamily?.title || 'this course family'}"?`}
      />
    </Box>
  );
};

export default CourseFamiliesPage;