import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import CourseFamilyForm from '../components/CourseFamilyForm';
import { useCourseFamilyQuery } from '../app/queries/courseFamilyQueries';
import { useOrganizationListQuery } from '../app/queries/organizationQueries';
import { courseFamilyService } from '../services/courseFamilyService';

const CourseFamilyEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const courseFamilyId = id ?? '';
  const navigate = useNavigate();

  const courseFamilyQuery = useCourseFamilyQuery(courseFamilyId, {
    enabled: Boolean(courseFamilyId),
  });

  const organizationListQuery = useOrganizationListQuery({ limit: 500 });

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (payload: any) => {
    if (!courseFamilyId) return;

    try {
      setSubmitting(true);
      setSubmitError(null);
      await courseFamilyService.updateCourseFamily(courseFamilyId, payload);
      navigate(`/admin/course-families/${courseFamilyId}`);
    } catch (error: any) {
      console.error('Error updating course family:', error);
      setSubmitError(error?.message || 'Failed to update course family');
    } finally {
      setSubmitting(false);
    }
  };

  if (courseFamilyQuery.isLoading || organizationListQuery.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (courseFamilyQuery.error || !courseFamilyQuery.data) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          {courseFamilyQuery.error instanceof Error
            ? courseFamilyQuery.error.message
            : 'Course family not found'}
        </Alert>
      </Box>
    );
  }

  const organizations = organizationListQuery.data?.items ?? [];

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h4">Edit Course Family</Typography>
          <Typography variant="body2" color="text.secondary">
            Update the metadata. Only modified fields will be persisted.
          </Typography>
        </Stack>
        <CourseFamilyForm
          courseFamily={courseFamilyQuery.data}
          organizations={organizations}
          mode="edit"
          onSubmit={handleSubmit}
          onClose={() => navigate(`/admin/course-families/${courseFamilyId}`)}
          loading={submitting}
          error={submitError}
        />
      </Paper>
    </Box>
  );
};

export default CourseFamilyEditPage;
