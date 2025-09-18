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
  AccountTree as AccountTreeIcon,
  ArrowBack as ArrowBackIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
  Group as GroupIcon,
  LocationOn as LocationIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  Web as WebIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { useOrganizationQuery } from '../app/queries/organizationQueries';
import { useCourseFamilyListQuery } from '../app/queries/courseFamilyQueries';

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

const OrganizationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const organizationId = id ?? '';
  const navigate = useNavigate();

  const organizationQuery = useOrganizationQuery(organizationId, {
    enabled: Boolean(organizationId),
  });

  const courseFamilyQuery = useCourseFamilyListQuery(
    {
      organization_id: organizationId,
      limit: 500,
    },
    {
      enabled: Boolean(organizationId),
    }
  );

  const organization = organizationQuery.data;
  const courseFamilies = courseFamilyQuery.data?.items ?? [];

  if (organizationQuery.isLoading || courseFamilyQuery.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (organizationQuery.error || !organization) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          {organizationQuery.error instanceof Error
            ? organizationQuery.error.message
            : 'Organization not found'}
        </Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/admin/organizations')}
          sx={{ mt: 2 }}
        >
          Back to Organizations
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/admin/organizations')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Organization Details</Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="outlined"
          startIcon={<AccountTreeIcon />}
          onClick={() => navigate(`/admin/organizations/${organization.id}/edit`)}
        >
          Edit Organization
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={3} alignItems="center">
              <Box sx={{ textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>{getOrgTypeIcon(organization.organization_type)}</Box>
                <Typography variant="h5">
                  {organization.title ||
                    `User Organization (${organization.user_id?.substring(0, 8)}...)`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {organization.path}
                </Typography>
              </Box>

              <Chip
                icon={getOrgTypeIcon(organization.organization_type)}
                label={organization.organization_type}
                size="small"
                variant="outlined"
              />

              <Stack spacing={1} sx={{ width: '100%' }}>
                {organization.email && (
                  <Stack direction="row" spacing={1} alignItems="center">
                    <EmailIcon fontSize="small" color="action" />
                    <Typography variant="body2">{organization.email}</Typography>
                  </Stack>
                )}
                {organization.telephone && (
                  <Stack direction="row" spacing={1} alignItems="center">
                    <PhoneIcon fontSize="small" color="action" />
                    <Typography variant="body2">{organization.telephone}</Typography>
                  </Stack>
                )}
                {organization.url && (
                  <Stack direction="row" spacing={1} alignItems="center">
                    <WebIcon fontSize="small" color="action" />
                    <Typography variant="body2">
                      <a href={organization.url} target="_blank" rel="noopener noreferrer">
                        {organization.url}
                      </a>
                    </Typography>
                  </Stack>
                )}
                {(organization.street_address ||
                  organization.locality ||
                  organization.region ||
                  organization.postal_code ||
                  organization.country) && (
                  <Stack direction="row" spacing={1} alignItems="flex-start">
                    <LocationIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      {[organization.street_address, organization.locality]
                        .filter(Boolean)
                        .join(', ')}
                      <br />
                      {[organization.region, organization.postal_code]
                        .filter(Boolean)
                        .join(' ')}
                      <br />
                      {organization.country}
                    </Typography>
                  </Stack>
                )}
              </Stack>
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Course Families
            </Typography>
            <Stack spacing={2}>
              {courseFamilyQuery.isFetching && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              )}

              {courseFamilyQuery.error instanceof Error && (
                <Alert severity="error">
                  {courseFamilyQuery.error.message}
                </Alert>
              )}

              {courseFamilies.length === 0 && !courseFamilyQuery.isFetching ? (
                <Typography variant="body2" color="text.secondary">
                  No course families found for this organization.
                </Typography>
              ) : (
                courseFamilies.map((family) => (
                  <Paper
                    key={family.id}
                    variant="outlined"
                    sx={{ p: 2, cursor: 'pointer' }}
                    onClick={() => navigate(`/admin/course-families/${family.id}`)}
                  >
                    <Stack spacing={0.5}>
                      <Typography variant="subtitle2">
                        {family.title || 'Untitled Course Family'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {family.path}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Created{' '}
                        {family.created_at
                          ? formatDistanceToNow(new Date(family.created_at), {
                              addSuffix: true,
                            })
                          : '—'}
                      </Typography>
                    </Stack>
                  </Paper>
                ))
              )}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default OrganizationDetailPage;
