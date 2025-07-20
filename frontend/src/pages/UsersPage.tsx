import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  Avatar,
  Stack,
  TextField,
  InputAdornment,
  Tooltip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  PersonAdd as PersonAddIcon,
} from '@mui/icons-material';
import { User, Account } from '../types';

interface UsersPageProps {}

// Mock data structure based on the database models
interface UserWithAccounts extends User {
  accounts: Account[];
  profile?: {
    avatar_color?: number;
    avatar_image?: string;
    nickname?: string;
    bio?: string;
  };
  student_profile?: {
    student_id?: string;
    student_email?: string;
  };
}

// Mock users data for development
const mockUsers: UserWithAccounts[] = [
  {
    id: '1',
    given_name: 'John',
    family_name: 'Doe',
    email: 'john.doe@university.edu',
    username: 'johndoe',
    user_type: 'user',
    fs_number: 1001,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
    archived_at: null,
    accounts: [
      {
        id: 'acc1',
        provider: 'keycloak',
        type: 'oidc',
        provider_account_id: 'kc_john_123',
        user_id: '1',
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-15T10:30:00Z',
      }
    ],
    profile: {
      nickname: 'Johnny',
      bio: 'Computer Science student',
      avatar_color: 1,
    },
    student_profile: {
      student_id: 'CS-2024-001',
      student_email: 'john.doe@student.university.edu',
    }
  },
  {
    id: '2',
    given_name: 'Jane',
    family_name: 'Smith',
    email: 'jane.smith@university.edu',
    username: 'janesmith',
    user_type: 'user',
    fs_number: 1002,
    created_at: '2024-01-16T14:20:00Z',
    updated_at: '2024-01-16T14:20:00Z',
    archived_at: null,
    accounts: [
      {
        id: 'acc2',
        provider: 'keycloak',
        type: 'oidc',
        provider_account_id: 'kc_jane_456',
        user_id: '2',
        created_at: '2024-01-16T14:20:00Z',
        updated_at: '2024-01-16T14:20:00Z',
      }
    ],
    profile: {
      nickname: 'Jane',
      bio: 'Mathematics professor',
      avatar_color: 2,
    }
  },
  {
    id: '3',
    given_name: 'Admin',
    family_name: 'User',
    email: 'admin@university.edu',
    username: 'admin',
    user_type: 'user',
    fs_number: 1000,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    archived_at: null,
    accounts: [
      {
        id: 'acc3',
        provider: 'basic',
        type: 'local',
        provider_account_id: 'admin_local',
        user_id: '3',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
    ],
    profile: {
      nickname: 'Admin',
      bio: 'System Administrator',
      avatar_color: 3,
    }
  }
];

const UsersPage: React.FC<UsersPageProps> = () => {
  const [users] = useState<UserWithAccounts[]>(mockUsers);
  const [loading] = useState(false);
  const [error] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Filter users based on search term
  const filteredUsers = users.filter(user =>
    user.given_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.family_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.student_profile?.student_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleEditUser = (userId: string) => {
    console.log('Edit user:', userId);
    // TODO: Implement edit user functionality
  };

  const handleDeleteUser = (userId: string) => {
    console.log('Delete user:', userId);
    // TODO: Implement delete user functionality with confirmation
  };

  const handleCreateUser = () => {
    console.log('Create new user');
    // TODO: Implement create user functionality
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getUserTypeColor = (userType: string) => {
    switch (userType) {
      case 'user': return 'primary';
      case 'token': return 'secondary';
      default: return 'default';
    }
  };

  const getAccountProviderColor = (provider: string) => {
    switch (provider) {
      case 'keycloak': return 'info';
      case 'basic': return 'default';
      default: return 'warning';
    }
  };

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  const getAvatarColor = (colorIndex?: number) => {
    const colors = [
      '#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5',
      '#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4caf50',
      '#8bc34a', '#cddc39', '#ffeb3b', '#ffc107', '#ff9800',
    ];
    return colors[colorIndex || 0] || colors[0];
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            User Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage users, accounts, and permissions across the system
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<PersonAddIcon />}
          onClick={handleCreateUser}
          size="large"
        >
          Create User
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            placeholder="Search users by name, email, username, or student ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            variant="outlined"
            size="small"
            sx={{ flexGrow: 1 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              },
            }}
          />
          <Typography variant="body2" color="text.secondary">
            {filteredUsers.length} user{filteredUsers.length !== 1 ? 's' : ''} found
          </Typography>
        </Stack>
      </Paper>

      {/* Users Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>User</TableCell>
                <TableCell>Username</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Student ID</TableCell>
                <TableCell>Accounts</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredUsers
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell>
                      <Stack direction="row" spacing={2} alignItems="center">
                        <Avatar
                          sx={{
                            bgcolor: getAvatarColor(user.profile?.avatar_color),
                            width: 40,
                            height: 40,
                          }}
                          src={user.profile?.avatar_image}
                        >
                          {getInitials(user.given_name, user.family_name)}
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle2">
                            {user.given_name} {user.family_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {user.email}
                          </Typography>
                          {user.profile?.nickname && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              "{user.profile.nickname}"
                            </Typography>
                          )}
                        </Box>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {user.username || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={user.user_type}
                        color={getUserTypeColor(user.user_type)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {user.student_profile?.student_id ? (
                        <Chip
                          label={user.student_profile.student_id}
                          variant="outlined"
                          size="small"
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap">
                        {user.accounts.map((account) => (
                          <Chip
                            key={account.id}
                            label={`${account.provider}:${account.type}`}
                            color={getAccountProviderColor(account.provider)}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(user.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={user.archived_at ? 'Archived' : 'Active'}
                        color={user.archived_at ? 'default' : 'success'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        <Tooltip title="Edit User">
                          <IconButton
                            size="small"
                            onClick={() => handleEditUser(user.id)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete User">
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteUser(user.id)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={filteredUsers.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      {/* Statistics Summary */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          User Statistics
        </Typography>
        <Stack direction="row" spacing={4}>
          <Box>
            <Typography variant="h4" color="primary">
              {users.filter(u => !u.archived_at).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Active Users
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="secondary">
              {users.filter(u => u.student_profile?.student_id).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Students
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="info.main">
              {users.filter(u => u.accounts.some(a => a.provider === 'keycloak')).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              SSO Users
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="warning.main">
              {users.filter(u => u.archived_at).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Archived
            </Typography>
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
};

export default UsersPage;