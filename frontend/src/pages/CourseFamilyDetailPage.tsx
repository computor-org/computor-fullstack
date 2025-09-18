import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Grid,
  IconButton,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Business as BusinessIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { useCourseFamilyQuery } from '../app/queries/courseFamilyQueries';
import { useOrganizationQuery } from '../app/queries/organizationQueries';

const CourseFamilyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const courseFamilyId = id ?? '';
  const navigate = useNavigate();

  const courseFamilyQuery = useCourseFamilyQuery(courseFamilyId, {
    enabled: Boolean(courseFamilyId),
  });

  const organizationId = courseFamilyQuery.data?.organization_id ?? '';
  const organizationQuery = useOrganizationQuery(organizationId, {
    enabled: Boolean(organizationId),
  });

  const courseFamily = courseFamilyQuery.data;

  if (courseFamilyQuery.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (courseFamilyQuery.error || !courseFamily) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          {courseFamilyQuery.error instanceof Error
            ? courseFamilyQuery.error.message
            : 'Course family not found'}
        </Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/admin/course-families')}
          sx={{ mt: 2 }}
        >
          Back to Course Families
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/admin/course-families')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Course Family Details</Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="outlined"
          onClick={() => navigate(`/admin/course-families/${courseFamily.id}/edit`)}
        >
          Edit Course Family
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={3} alignItems="center">
              <Box sx={{ textAlign: 'center' }}>
                <SchoolIcon fontSize="large" color="primary" />
                <Typography variant="h5" sx={{ mt: 2 }}>
                  {courseFamily.title || 'Untitled Course Family'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {courseFamily.path}
                </Typography>
              </Box>

              {courseFamily.description && (
                <Typography variant="body2" color="text.secondary" textAlign="center">
                  {courseFamily.description}
                </Typography>
              )}

              {courseFamily.organization_id && (
                <Paper variant="outlined" sx={{ p: 2, width: '100%' }}>
                  <Stack spacing={1}>
                    <Typography variant="subtitle2">Organization</Typography>
                    {organizationQuery.isLoading && (
                      <CircularProgress size={18} />
                    )}
                    {organizationQuery.data && (
                      <Stack direction="row" spacing={1} alignItems="center">
                        <BusinessIcon fontSize="small" color="action" />
                        <Typography variant="body2">
                          {organizationQuery.data.title || organizationQuery.data.path}
                        </Typography>
                      </Stack>
                    )}
                  </Stack>
                </Paper>
              )}

              <Stack direction="row" spacing={1}>
                <Chip
                  label={`Created ${
                    courseFamily.created_at
                      ? formatDistanceToNow(new Date(courseFamily.created_at), {
                          addSuffix: true,
                        })
                      : '—'
                  }`}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={`Updated ${
                    courseFamily.updated_at
                      ? formatDistanceToNow(new Date(courseFamily.updated_at), {
                          addSuffix: true,
                        })
                      : '—'
                  }`}
                  size="small"
                  variant="outlined"
                />
              </Stack>
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Courses
            </Typography>
            <Typography variant="body2" color="text.secondary">
              No courses linked to this course family yet.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CourseFamilyDetailPage;
