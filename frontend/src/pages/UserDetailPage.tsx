import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Avatar,
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
  AccountCircle as AccountIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { UserGet, UserRoleGet, AccountGet } from '../types/generated/users';
import { RoleGet } from '../types/generated/roles';
import { apiClient } from '../services/apiClient';
import { DataTable, Column } from '../components/common/DataTable';
import { formatDistanceToNow } from 'date-fns';

interface UserRoleWithDetails extends UserRoleGet {
  role?: RoleGet;
}

interface UserDetailData extends UserGet {
  accounts: AccountGet[];
  roles: UserRoleWithDetails[];
}

const UserDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [user, setUser] = useState<UserDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUserDetails();
  }, [id]);

  const loadUserDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load user details
      const userData = await apiClient.get<any>(`/users/${id}`);
      
      // Load user accounts
      let accountsData: any[] = [];
      try {
        accountsData = await apiClient.get<any[]>(`/accounts?user_id=${id}`);
        console.log('Accounts data loaded:', accountsData);
      } catch (accountError) {
        console.error('Error loading accounts:', accountError);
        // Continue with empty accounts array if accounts API fails
        accountsData = [];
      }
      
      // Load user roles
      const rolesData = await apiClient.get<any[]>(`/user-roles?user_id=${id}`);
      
      // Load role details for each user role
      const rolesWithDetails = await Promise.all(
        rolesData.map(async (userRole) => {
          try {
            const roleDetail = await apiClient.get<any>(`/roles/${userRole.role_id}`);
            return { ...userRole, role: roleDetail };
          } catch {
            return userRole;
          }
        })
      );

      setUser({
        ...userData,
        accounts: accountsData || [],
        roles: rolesWithDetails,
      });
    } catch (err) {
      console.error('Error loading user details:', err);
      setError('Failed to load user details');
    } finally {
      setLoading(false);
    }
  };

  const accountColumns: Column<AccountGet>[] = [
    {
      id: 'provider',
      label: 'Provider',
      render: (value) => (
        <Chip 
          label={value} 
          size="small" 
          color={value === 'keycloak' ? 'primary' : 'default'}
        />
      ),
    },
    {
      id: 'type',
      label: 'Type',
      render: (value) => value.toUpperCase(),
    },
    {
      id: 'provider_account_id',
      label: 'Account ID',
    },
    {
      id: 'created_at',
      label: 'Created',
      render: (value) => value ? formatDistanceToNow(new Date(value), { addSuffix: true }) : '-',
    },
  ];

  const roleColumns: Column<UserRoleWithDetails>[] = [
    {
      id: 'role',
      label: 'Role',
      accessor: (row) => row.role?.title || row.role_id,
      render: (value, row) => (
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography>{value}</Typography>
          {row.role?.builtin && (
            <Chip label="Built-in" size="small" variant="outlined" />
          )}
        </Stack>
      ),
    },
    {
      id: 'description',
      label: 'Description',
      accessor: (row) => row.role?.description || '-',
    },
  ];

  const getAvatarColor = () => {
    const colors = ['#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3'];
    const index = user?.number ? parseInt(user.number) % colors.length : 0;
    return colors[index];
  };

  const getInitials = () => {
    if (!user) return '?';
    const first = user.given_name?.[0] || '';
    const last = user.family_name?.[0] || '';
    return (first + last).toUpperCase() || user.username?.[0]?.toUpperCase() || '?';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !user) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error || 'User not found'}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin/users')} sx={{ mt: 2 }}>
          Back to Users
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/admin/users')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">User Details</Typography>
      </Box>

      <Grid container spacing={3}>
        {/* User Information Card */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={3} alignItems="center">
              <Avatar
                sx={{
                  width: 120,
                  height: 120,
                  bgcolor: getAvatarColor(),
                  fontSize: '3rem',
                }}
              >
                {getInitials()}
              </Avatar>

              <Box textAlign="center">
                <Typography variant="h5">
                  {user.given_name} {user.family_name}
                </Typography>
              </Box>

              <Divider sx={{ width: '100%' }} />

              <Box sx={{ width: '100%' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Email
                </Typography>
                <Typography>{user.email}</Typography>
              </Box>

              {user.username && (
                <Box sx={{ width: '100%' }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Username
                  </Typography>
                  <Typography>{user.username}</Typography>
                </Box>
              )}

              <Box sx={{ width: '100%' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  User Type
                </Typography>
                <Chip 
                  label={user.user_type} 
                  size="small" 
                  color={user.user_type === 'token' ? 'warning' : 'primary'}
                />
              </Box>


              <Divider sx={{ width: '100%' }} />

              <Button
                fullWidth
                variant="contained"
                startIcon={<EditIcon />}
                onClick={() => navigate(`/admin/users/${id}/edit`)}
              >
                Edit User
              </Button>
            </Stack>
          </Paper>
        </Grid>

        {/* Accounts and Roles */}
        <Grid item xs={12} md={8}>
          <Stack spacing={3}>
            {/* Authentication Accounts */}
            <DataTable
              title="Authentication Accounts"
              columns={accountColumns}
              data={user.accounts}
              page={0}
              rowsPerPage={10}
              onPageChange={() => {}}
              onRowsPerPageChange={() => {}}
              actions={
                <Button
                  size="small"
                  startIcon={<AccountIcon />}
                  onClick={() => {/* TODO: Add account linking */}}
                >
                  Link Account
                </Button>
              }
              emptyMessage="No authentication accounts linked"
            />

            {/* User Roles */}
            <DataTable
              title="User Roles"
              columns={roleColumns}
              data={user.roles.map(role => ({ ...role, id: `${role.user_id}-${role.role_id}` }))}
              page={0}
              rowsPerPage={10}
              onPageChange={() => {}}
              onRowsPerPageChange={() => {}}
              actions={
                <Button
                  size="small"
                  startIcon={<SecurityIcon />}
                  onClick={() => {/* TODO: Add role assignment */}}
                >
                  Assign Role
                </Button>
              }
              emptyMessage="No roles assigned"
            />
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
};

export default UserDetailPage;