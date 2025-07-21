import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  Stack,
  Divider,
  Alert,
  CircularProgress,
  IconButton,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  School as SchoolIcon,
  Business as BusinessIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { CourseFamilyGet } from '../types/generated/courses';
import { OrganizationGet } from '../types/generated/organizations';
import { apiClient } from '../services/apiClient';
import { DataTable, Column } from '../components/common/DataTable';
import { formatDistanceToNow } from 'date-fns';

const CourseFamilyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [courseFamily, setCourseFamily] = useState<CourseFamilyGet | null>(null);
  const [organization, setOrganization] = useState<OrganizationGet | null>(null);
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCourseFamilyDetails();
  }, [id]);

  const loadCourseFamilyDetails = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      // Load course family details
      const cfData = await apiClient.get<CourseFamilyGet>(`/course-families/${id}`);
      setCourseFamily(cfData);

      // Load organization details
      if (cfData.organization_id) {
        try {
          const orgData = await apiClient.get<OrganizationGet>(`/organizations/${cfData.organization_id}`);
          setOrganization(orgData);
        } catch (orgError) {
          console.error('Error loading organization:', orgError);
          setOrganization(null);
        }
      }

      // Load courses for this course family (when courses API is available)
      try {
        // const coursesData = await apiClient.get<any[]>(`/courses?course_family_id=${id}`);
        // setCourses(coursesData || []);
        setCourses([]); // For now, empty until courses API is implemented
      } catch (coursesError) {
        console.error('Error loading courses:', coursesError);
        setCourses([]);
      }
    } catch (err: any) {
      console.error('Error loading course family details:', err);
      setError('Failed to load course family details');
    } finally {
      setLoading(false);
    }
  };

  const coursesColumns: Column<any>[] = [
    {
      id: 'title',
      label: 'Course',
      render: (value, row) => (
        <Box>
          <Typography variant="subtitle2">
            {value || 'Untitled Course'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {row.code}
          </Typography>
        </Box>
      ),
    },
    {
      id: 'description',
      label: 'Description',
      render: (value) => (
        <Typography variant="body2" color="text.secondary">
          {value || '-'}
        </Typography>
      ),
    },
    {
      id: 'status',
      label: 'Status',
      render: (value) => (
        <Chip 
          label={value || 'Draft'} 
          size="small" 
          color={value === 'active' ? 'success' : 'default'}
        />
      ),
    },
    {
      id: 'created_at',
      label: 'Created',
      render: (value) => formatDistanceToNow(new Date(value), { addSuffix: true }),
    },
  ];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !courseFamily) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error || 'Course family not found'}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin/course-families')} sx={{ mt: 2 }}>
          Back to Course Families
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/admin/course-families')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Course Family Details</Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Course Family Information Card */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={3} alignItems="center">
              <Box sx={{ textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>
                  <SchoolIcon fontSize="large" color="primary" />
                </Box>
                <Typography variant="h5">
                  {courseFamily.title || 'Untitled Course Family'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {courseFamily.path}
                </Typography>
              </Box>

              {courseFamily.description && (
                <>
                  <Divider sx={{ width: '100%' }} />
                  <Box sx={{ width: '100%' }}>
                    <Typography variant="h6" gutterBottom>
                      Description
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {courseFamily.description}
                    </Typography>
                  </Box>
                </>
              )}

              {/* Organization Information */}
              {organization && (
                <>
                  <Divider sx={{ width: '100%' }} />
                  <Box sx={{ width: '100%' }}>
                    <Typography variant="h6" gutterBottom>
                      Organization
                    </Typography>
                    <Box 
                      sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 1, 
                        p: 2, 
                        bgcolor: 'grey.50', 
                        borderRadius: 1,
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'grey.100' }
                      }}
                      onClick={() => navigate(`/admin/organizations/${organization.id}`)}
                    >
                      <BusinessIcon fontSize="small" color="action" />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle2">
                          {organization.title || `User Organization (${organization.user_id?.substring(0, 8)}...)`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {organization.path}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </>
              )}

              {/* Metadata */}
              <Divider sx={{ width: '100%' }} />
              <Box sx={{ width: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Metadata
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Created:</strong> {formatDistanceToNow(new Date(courseFamily.created_at || ''), { addSuffix: true })}
                </Typography>
                {courseFamily.updated_at && courseFamily.updated_at !== courseFamily.created_at && (
                  <Typography variant="body2" color="text.secondary">
                    <strong>Updated:</strong> {formatDistanceToNow(new Date(courseFamily.updated_at), { addSuffix: true })}
                  </Typography>
                )}
              </Box>

              <Divider sx={{ width: '100%' }} />

              <Button
                fullWidth
                variant="contained"
                startIcon={<EditIcon />}
                onClick={() => navigate(`/admin/course-families/${id}/edit`)}
              >
                Edit Course Family
              </Button>
            </Stack>
          </Paper>
        </Grid>

        {/* Courses */}
        <Grid item xs={12} md={8}>
          <Stack spacing={3}>
            <DataTable
              title="Courses"
              columns={coursesColumns}
              data={courses.map(course => ({ ...course, id: course.id || `course-${Math.random()}` }))}
              loading={false}
              error={null}
              page={0}
              rowsPerPage={10}
              onPageChange={() => {}}
              onRowsPerPageChange={() => {}}
              totalCount={courses.length}
              onRowClick={(course) => navigate(`/admin/courses/${course.id}`)}
              emptyMessage="No courses found for this course family. Courses will be displayed here when the courses management system is implemented."
            />
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CourseFamilyDetailPage;