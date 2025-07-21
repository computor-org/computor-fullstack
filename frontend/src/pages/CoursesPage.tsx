import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
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
import { CourseGet, CourseCreate, CourseUpdate } from '../types/generated/courses';
import { apiClient } from '../services/apiClient';
import { DataTable, Column } from '../components/common/DataTable';
import { FormDialog } from '../components/common/FormDialog';
import CourseTaskForm from '../components/CourseTaskForm';
import DeleteDialog from '../components/DeleteDialog';

const CoursesPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [courses, setCourses] = useState<CourseGet[]>([]);
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
  const [selectedCourse, setSelectedCourse] = useState<CourseGet | null>(null);
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

  // Load courses
  const loadCourses = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.get<any>('/courses', {
        params: {
          limit: rowsPerPage,
          offset: page * rowsPerPage,
          ...(searchTerm && { title: searchTerm }),
        },
        headers: {
          'Cache-Control': 'no-cache',
        },
      });

      const total = response.headers?.['x-total-count'] || response.data?.length || 0;
      const data = Array.isArray(response) ? response : response.data || [];

      setCourses(data);
      setTotalCount(parseInt(total, 10));
    } catch (err: any) {
      console.error('Error loading courses:', err);
      setError(err.message || 'Failed to load courses');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, searchTerm]);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  // Check for refresh parameter and clear it
  useEffect(() => {
    if (searchParams.get('refresh')) {
      setSearchParams({});
      loadCourses();
    }
  }, [searchParams, setSearchParams, loadCourses]);

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
    try {
      setFormLoading(true);
      if (selectedCourse) {
        await apiClient.patch(`/courses/${selectedCourse.id}`, data);
      }
      setFormOpen(false);
      loadCourses();
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
      await apiClient.delete(`/courses/${selectedCourse.id}`);
      setDeleteOpen(false);
      loadCourses();
    } catch (err: any) {
      console.error('Error deleting course:', err);
      alert(err.message || 'Failed to delete course');
    }
  };

  const columns: Column<CourseGet>[] = [
    {
      id: 'title',
      label: 'Course',
      render: (value, row) => (
        <Box>
          <Typography variant="subtitle2">
            {value || 'Untitled Course'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {row.path}
          </Typography>
        </Box>
      ),
    },
    {
      id: 'course_family',
      label: 'Course Family',
      accessor: (row) => row.course_family?.title || '-',
      render: (value, row) => (
        <Stack direction="row" spacing={1} alignItems="center">
          <SchoolIcon fontSize="small" color="action" />
          <Box>
            <Typography variant="body2">{value}</Typography>
            {row.course_family?.organization && (
              <Typography variant="caption" color="text.secondary">
                {row.course_family.organization.title}
              </Typography>
            )}
          </Box>
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

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <DataTable
        title="Courses"
        columns={columns}
        data={courses}
        loading={loading}
        error={null}
        totalCount={totalCount}
        page={page}
        rowsPerPage={rowsPerPage}
        searchValue={searchValue}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        onSearchChange={setSearchValue}
        onRefresh={loadCourses}
        onRowClick={(course) => navigate(`/admin/courses/${course.id}`)}
        rowActions={rowActions}
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Add Course
          </Button>
        }
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title="Edit Course"
        loading={formLoading}
        maxWidth="md"
      >
        <CourseTaskForm
          course={selectedCourse}
          mode="edit"
          onSubmit={handleFormSubmit}
          onClose={() => setFormOpen(false)}
        />
      </FormDialog>

      <DeleteDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Course"
        message={`Are you sure you want to delete "${selectedCourse?.title || 'this course'}"?`}
      />
    </Box>
  );
};

export default CoursesPage;