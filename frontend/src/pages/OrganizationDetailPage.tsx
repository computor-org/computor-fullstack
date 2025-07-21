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
  Business as BusinessIcon,
  Group as GroupIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Web as WebIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import { OrganizationGet } from '../types/generated/organizations';
import { CourseFamilyGet } from '../types/generated/courses';
import { apiClient } from '../services/apiClient';
import { DataTable, Column } from '../components/common/DataTable';
import { formatDistanceToNow } from 'date-fns';

const OrganizationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [organization, setOrganization] = useState<OrganizationGet | null>(null);
  const [courseFamilies, setCourseFamilies] = useState<CourseFamilyGet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOrganizationDetails();
  }, [id]);

  const loadOrganizationDetails = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      // Load organization details
      const orgData = await apiClient.get<OrganizationGet>(`/organizations/${id}`);
      setOrganization(orgData);

      // Load course families for this organization
      try {
        const courseFamiliesData = await apiClient.get<CourseFamilyGet[]>(`/course-families?organization_id=${id}`);
        setCourseFamilies(courseFamiliesData || []);
      } catch (cfError) {
        console.error('Error loading course families:', cfError);
        // Continue with empty course families if API fails
        setCourseFamilies([]);
      }
    } catch (err: any) {
      console.error('Error loading organization details:', err);
      setError('Failed to load organization details');
    } finally {
      setLoading(false);
    }
  };

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

  const courseFamilyColumns: Column<CourseFamilyGet>[] = [
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
      id: 'description',
      label: 'Description',
      render: (value) => (
        <Typography variant="body2" color="text.secondary">
          {value || '-'}
        </Typography>
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

  if (error || !organization) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error || 'Organization not found'}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin/organizations')} sx={{ mt: 2 }}>
          Back to Organizations
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/admin/organizations')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Organization Details</Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Organization Information Card */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={3} alignItems="center">
              <Box sx={{ textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>
                  {getOrgTypeIcon(organization.organization_type)}
                </Box>
                <Typography variant="h5">
                  {organization.title || `User Organization (${organization.user_id?.substring(0, 8)}...)`}
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

              <Divider sx={{ width: '100%' }} />

              {/* Contact Information */}
              <Box sx={{ width: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Contact Information
                </Typography>
                
                {organization.email && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <EmailIcon fontSize="small" color="action" />
                    <Typography variant="body2">{organization.email}</Typography>
                  </Box>
                )}
                
                {organization.telephone && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <PhoneIcon fontSize="small" color="action" />
                    <Typography variant="body2">{organization.telephone}</Typography>
                  </Box>
                )}
                
                {organization.url && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <WebIcon fontSize="small" color="action" />
                    <Typography variant="body2">
                      <a href={organization.url} target="_blank" rel="noopener noreferrer">
                        {organization.url}
                      </a>
                    </Typography>
                  </Box>
                )}
              </Box>

              {/* Location Information */}
              {(organization.street_address || organization.locality || organization.region || organization.country) && (
                <>
                  <Divider sx={{ width: '100%' }} />
                  <Box sx={{ width: '100%' }}>
                    <Typography variant="h6" gutterBottom>
                      <LocationIcon fontSize="small" sx={{ mr: 1 }} />
                      Location
                    </Typography>
                    
                    {organization.street_address && (
                      <Typography variant="body2" color="text.secondary">
                        {organization.street_address}
                      </Typography>
                    )}
                    
                    <Typography variant="body2" color="text.secondary">
                      {[organization.locality, organization.region, organization.postal_code, organization.country]
                        .filter(Boolean)
                        .join(', ')}
                    </Typography>
                  </Box>
                </>
              )}

              <Divider sx={{ width: '100%' }} />

              <Button
                fullWidth
                variant="contained"
                startIcon={<EditIcon />}
                onClick={() => navigate(`/admin/organizations/${id}/edit`)}
              >
                Edit Organization
              </Button>
            </Stack>
          </Paper>
        </Grid>

        {/* Course Families */}
        <Grid item xs={12} md={8}>
          <Stack spacing={3}>
            <DataTable
              title="Course Families"
              columns={courseFamilyColumns}
              data={courseFamilies.map(cf => ({ ...cf, id: cf.id }))}
              loading={false}
              error={null}
              page={0}
              rowsPerPage={10}
              onPageChange={() => {}}
              onRowsPerPageChange={() => {}}
              totalCount={courseFamilies.length}
              onRowClick={(cf) => navigate(`/admin/course-families/${cf.id}`)}
              emptyMessage="No course families found for this organization"
            />
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
};

export default OrganizationDetailPage;