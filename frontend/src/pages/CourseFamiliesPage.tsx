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
  AccountTree as AccountTreeIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useQueryClient } from '@tanstack/react-query';
import { CourseFamilyCreate, CourseFamilyGet, CourseFamilyUpdate } from '../types/generated/courses';
import { OrganizationGet } from '../types/generated/organizations';
import { DataTable, Column } from '../components/common/DataTable';
import { FormDialog } from '../components/common/FormDialog';
import CourseFamilyForm from '../components/CourseFamilyForm';
import DeleteDialog from '../components/DeleteDialog';
import { useCourseFamilyListQuery, courseFamilyKeys } from '../app/queries/courseFamilyQueries';
import { courseFamilyService } from '../services/courseFamilyService';
import { useOrganizationListQuery, organizationKeys } from '../app/queries/organizationQueries';

const CourseFamiliesPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchValue, setSearchValue] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedCourseFamily, setSelectedCourseFamily] = useState<CourseFamilyGet | null>(null);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [formLoading, setFormLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

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

  const courseFamilyListQuery = useCourseFamilyListQuery(queryParams);
  const { data, isLoading, isFetching, error } = courseFamilyListQuery;

  const organizationListQuery = useOrganizationListQuery({ limit: 500 });
  const organizations = (organizationListQuery.data?.items ?? []) as OrganizationGet[];

  const courseFamilies = data?.items ?? [];
  const totalCount = data?.total ?? 0;
  const errorMessage = error instanceof Error ? error.message : null;

  const handleCreate = () => {
    setSelectedCourseFamily(null);
    setFormMode('create');
    setFormOpen(true);
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

  const handleFormSubmit = async (payload: CourseFamilyCreate | CourseFamilyUpdate) => {
    try {
      setFormLoading(true);
      setFormError(null);
      if (formMode === 'edit' && selectedCourseFamily) {
        await courseFamilyService.updateCourseFamily(selectedCourseFamily.id, payload as CourseFamilyUpdate);
      } else {
        await courseFamilyService.createCourseFamily(payload as CourseFamilyCreate);
      }

      setFormOpen(false);
      setSelectedCourseFamily(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: courseFamilyKeys.all }),
        queryClient.invalidateQueries({ queryKey: organizationKeys.all }),
      ]);
    } catch (err: any) {
      console.error('Error saving course family:', err);
      setFormError(err?.message || 'Failed to save course family');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedCourseFamily) return;

    try {
      setDeleteLoading(true);
      await courseFamilyService.deleteCourseFamily(selectedCourseFamily.id);
      setDeleteOpen(false);
      setSelectedCourseFamily(null);
      await queryClient.invalidateQueries({ queryKey: courseFamilyKeys.all });
    } catch (err: any) {
      console.error('Error deleting course family:', err);
      alert(err.message || 'Failed to delete course family');
    } finally {
      setDeleteLoading(false);
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
      id: 'organization_id',
      label: 'Organization',
      render: (value, row) => (
        <Stack direction="row" spacing={1} alignItems="center">
          <BusinessIcon fontSize="small" color="action" />
          <Typography variant="body2">
            {row.organization?.title || value}
          </Typography>
        </Stack>
      ),
    },
    {
      id: 'description',
      label: 'Description',
      render: (value) => (
        <Typography variant="body2" color="text.secondary" noWrap>
          {value || '—'}
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
        Course Families
      </Typography>

      {organizationListQuery.error instanceof Error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Failed to load organizations list. Some dropdowns may be incomplete.
        </Alert>
      )}

      <DataTable
        title="Course Families"
        columns={columns}
        data={courseFamilies}
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
        onRefresh={() => courseFamilyListQuery.refetch()}
        onRowClick={(courseFamily) => navigate(`/admin/course-families/${courseFamily.id}`)}
        rowActions={rowActions}
        actions={
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
            Add Course Family
          </Button>
        }
      />

      <FormDialog
        open={formOpen}
        title={formMode === 'create' ? 'Create Course Family' : 'Edit Course Family'}
        onClose={() => {
          setFormOpen(false);
          setSelectedCourseFamily(null);
          setFormError(null);
        }}
        loading={formLoading || organizationListQuery.isLoading}
      >
        <CourseFamilyForm
          courseFamily={selectedCourseFamily}
          organizations={organizations}
          mode={formMode}
          onSubmit={handleFormSubmit}
          onClose={() => {
            setFormOpen(false);
            setSelectedCourseFamily(null);
            setFormError(null);
          }}
          loading={formLoading || organizationListQuery.isLoading}
          error={formError}
        />
      </FormDialog>

      <DeleteDialog
        open={deleteOpen}
        title="Delete Course Family"
        message={`Are you sure you want to delete ${selectedCourseFamily?.title || 'this course family'}?`}
        onClose={() => {
          setDeleteOpen(false);
          setSelectedCourseFamily(null);
        }}
        onConfirm={handleDeleteConfirm}
        loading={deleteLoading}
      />
    </Box>
  );
};

export default CourseFamiliesPage;
