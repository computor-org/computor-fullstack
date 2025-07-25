import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { UserGet, AccountGet } from '../types/generated/users';
import { apiClient } from '../services/apiClient';
import UserDialog from '../components/UserDialog';
import DeleteUserDialog from '../components/DeleteUserDialog';

interface UsersPageProps {}

// Extended user type with accounts
interface UserWithAccounts extends UserGet {
  accounts: AccountGet[];
  profile?: {
    avatar_color?: number;
    avatar_image?: string;
    nickname?: string;
    bio?: string;
  };
}


const UsersPage: React.FC<UsersPageProps> = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserWithAccounts[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalUsers, setTotalUsers] = useState(0);
  
  // Dialog states
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserWithAccounts | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');

  // Load users from API
  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.listUsers({
        limit: rowsPerPage,
        offset: page * rowsPerPage,
        search: searchTerm || undefined,
        archived: false
      });
      
      // Transform API response to match our interface
      const transformedUsers = response.map((user: any) => ({
        id: user.id,
        given_name: user.given_name || '',
        family_name: user.family_name || '',
        email: user.email || '',
        username: user.username,
        user_type: user.user_type || 'user',
        fs_number: user.fs_number || 0,
        created_at: user.created_at || new Date().toISOString(),
        updated_at: user.updated_at || new Date().toISOString(),
        archived_at: user.archived_at,
        accounts: user.accounts || [],
        profile: user.profile
      }));
      
      setUsers(transformedUsers);
      setTotalUsers(response.length); // Note: This might need to be adjusted based on actual API response
    } catch (err) {
      console.error('Error loading users:', err);
      setError('Failed to load users. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Debounce search input
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setSearchTerm(searchInput);
      setPage(0); // Reset to first page when searching
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchInput]);

  // Load users on component mount and when dependencies change
  useEffect(() => {
    loadUsers();
  }, [page, rowsPerPage, searchTerm]); // eslint-disable-line react-hooks/exhaustive-deps

  // For display purposes, we show all loaded users (no client-side filtering since server handles search)
  const displayUsers = users;

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleEditUser = (userId: string) => {
    const user = displayUsers.find(u => u.id === userId);
    if (user) {
      setSelectedUser(user);
      setDialogMode('edit');
      setUserDialogOpen(true);
    }
  };

  const handleDeleteUser = (userId: string) => {
    const user = displayUsers.find(u => u.id === userId);
    if (user) {
      setSelectedUser(user);
      setDeleteDialogOpen(true);
    }
  };

  const handleCreateUser = () => {
    setSelectedUser(null);
    setDialogMode('create');
    setUserDialogOpen(true);
  };

  const handleDialogSuccess = () => {
    // Reload users after successful create/update/delete
    loadUsers();
  };

  const handleCloseUserDialog = () => {
    setUserDialogOpen(false);
    setSelectedUser(null);
  };

  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setSelectedUser(null);
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
            placeholder="Search users by name, email, or username..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
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
            {displayUsers.length} user{displayUsers.length !== 1 ? 's' : ''} found
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
                  <TableCell>Created</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {displayUsers.map((user) => (
                  <TableRow 
                    key={user.id} 
                    hover
                    onClick={() => navigate(`/admin/users/${user.id}`)}
                    sx={{ cursor: 'pointer' }}
                  >
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
                          {getInitials(user.given_name || '', user.family_name || '')}
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
                      <Typography variant="body2">
                        {formatDate(user.created_at || '')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={user.archived_at ? 'Archived' : 'Active'}
                        color={user.archived_at ? 'default' : 'success'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right" onClick={(e) => e.stopPropagation()}>
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
          count={totalUsers}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>


      {/* User Create/Edit Dialog */}
      <UserDialog
        open={userDialogOpen}
        onClose={handleCloseUserDialog}
        onSuccess={handleDialogSuccess}
        user={selectedUser}
        mode={dialogMode}
      />

      {/* Delete User Dialog */}
      <DeleteUserDialog
        open={deleteDialogOpen}
        onClose={handleCloseDeleteDialog}
        onSuccess={handleDialogSuccess}
        user={selectedUser}
      />
    </Box>
  );
};

export default UsersPage;