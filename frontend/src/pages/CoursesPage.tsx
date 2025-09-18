import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
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
  School as SchoolIcon,
} from '@mui/icons-material';
import { useQueryClient } from '@tanstack/react-query';
import { CourseGet, CourseUpdate } from '../types/generated/courses';
import { DataTable, Column } from '../components/common/DataTable';
import { FormDialog } from '../components/common/FormDialog';
import CourseTaskForm from '../components/CourseTaskForm';
import DeleteDialog from '../components/DeleteDialog';
import { useCourseListQuery, courseKeys } from '../app/queries/courseQueries';
import { courseService } from '../services/courseService';

const CoursesPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchValue, setSearchValue] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState<CourseGet | null>(null);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
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

  const courseListQuery = useCourseListQuery(queryParams);
  const { data, isLoading, isFetching, error } = courseListQuery;

  const courses = data?.items ?? [];
  const totalCount = data?.total ?? 0;
  const errorMessage = error instanceof Error ? error.message : null;

  useEffect(() => {
    if (searchParams.get('refresh')) {
      setSearchParams({});
      queryClient.invalidateQueries({ queryKey: courseKeys.all });
    }
  }, [searchParams, setSearchParams, queryClient]);

  const handleCreate = () => {
    navigate('/admin/courses/create');
  };

  const handleEdit = (course: CourseGet) => {
    setSelectedCourse(course);
    setFormMode('edit');
    setFormOpen(true);
  };

  const handleDelete = (course: CourseGet) => {
    setSelectedCourse(course);
    setDeleteOpen(true);
  };

  const handleFormSubmit = async (data: CourseUpdate) => {
    if (!selectedCourse) return;

    try {
      setFormLoading(true);
      await courseService.updateCourse(selectedCourse.id, data);
      setFormOpen(false);
      setSelectedCourse(null);
      await queryClient.invalidateQueries({ queryKey: courseKeys.all });
    } catch (err: any) {
      console.error('Error saving course:', err);
      alert(err.message || 'Failed to save course');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedCourse) return;

    try {
      setDeleteLoading(true);
      await courseService.deleteCourse(selectedCourse.id);
      setDeleteOpen(false);
      setSelectedCourse(null);
      await queryClient.invalidateQueries({ queryKey: courseKeys.all });
    } catch (err: any) {
      console.error('Error deleting course:', err);
      alert(err.message || 'Failed to delete course');
    } finally {
      setDeleteLoading(false);
    }
  };

  const columns: Column<CourseGet>[] = [
    {
      id: 'title',
      label: 'Course',
      render: (value) => (
        <Typography variant="subtitle2">
          {value || 'Untitled Course'}
        </Typography>
      ),
    },
    {
      id: 'path',
      label: 'Path',
      render: (value) => (
        <Typography variant="body2" color="text.secondary">
          {value}
        </Typography>
      ),
    },
    {
      id: 'course_family_id',
      label: 'Course Family ID',
      render: (value) => (
        <Stack direction="row" spacing={1} alignItems="center">
          <SchoolIcon fontSize="small" color="action" />
          <Typography variant="body2">{value}</Typography>
        </Stack>
      ),
    },
    {
      id: 'properties',
      label: 'GitLab',
      render: (value) => {
        const hasGitlab = value?.gitlab?.group_id;
        return (
          <Chip
            label={hasGitlab ? 'Enabled' : 'Disabled'}
            color={hasGitlab ? 'success' : 'default'}
            size="small"
            variant="outlined"
          />
        );
      },
    },
  ];

  const rowActions = (row: CourseGet) => (
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
        Courses Management
      </Typography>

      <DataTable
        title="Courses"
        columns={columns}
        data={courses}
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
        onRefresh={() => courseListQuery.refetch()}
        onRowClick={(course) => navigate(`/admin/courses/${course.id}`)}
        rowActions={rowActions}
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Create Course
          </Button>
        }
      />

      <FormDialog
        open={formOpen}
        title={formMode === 'create' ? 'Create Course' : 'Edit Course'}
        onClose={() => {
          setFormOpen(false);
          setSelectedCourse(null);
        }}
        loading={formLoading}
      >
        <CourseTaskForm
          course={selectedCourse}
          mode={formMode}
          onSubmit={handleFormSubmit}
          hideStatusAlerts
        />
      </FormDialog>

      <DeleteDialog
        open={deleteOpen}
        title="Delete Course"
        message={`Are you sure you want to delete ${selectedCourse?.title || 'this course'}?`}
        onClose={() => {
          setDeleteOpen(false);
          setSelectedCourse(null);
        }}
        onConfirm={handleDeleteConfirm}
        loading={deleteLoading}
      />
    </Box>
  );
};

export default CoursesPage;
