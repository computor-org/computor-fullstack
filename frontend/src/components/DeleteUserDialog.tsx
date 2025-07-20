import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Box,
  Chip,
} from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';
import { User } from '../types';
import { apiClient } from '../services/apiClient';

interface DeleteUserDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  user: User | null;
}

const DeleteUserDialog: React.FC<DeleteUserDialogProps> = ({
  open,
  onClose,
  onSuccess,
  user
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!user) return;

    setLoading(true);
    setError(null);

    try {
      await apiClient.deleteUser(user.id);
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Error deleting user:', err);
      
      if (err.message.includes('403')) {
        setError('You do not have permission to delete this user');
      } else if (err.message.includes('409') || err.message.includes('conflict')) {
        setError('Cannot delete user. They may have associated data (courses, submissions, etc.)');
      } else if (err.message.includes('404')) {
        setError('User not found. They may have already been deleted.');
      } else {
        setError('Failed to delete user. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      onClose();
    }
  };

  if (!user) return null;

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <WarningIcon color="error" />
        <Typography variant="h6">
          Delete User
        </Typography>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Typography variant="body1" gutterBottom>
          Are you sure you want to delete this user? This action cannot be undone.
        </Typography>

        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            User Details:
          </Typography>
          <Typography variant="body2">
            <strong>Name:</strong> {user.given_name} {user.family_name}
          </Typography>
          <Typography variant="body2">
            <strong>Email:</strong> {user.email}
          </Typography>
          <Typography variant="body2">
            <strong>Username:</strong> {user.username || 'N/A'}
          </Typography>
          <Box sx={{ mt: 1 }}>
            <Chip 
              label={user.user_type} 
              size="small" 
              color={user.user_type === 'user' ? 'primary' : 'secondary'} 
            />
          </Box>
        </Box>

        <Alert severity="warning" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Warning:</strong> Deleting this user will:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li>Remove all user data permanently</li>
            <li>Remove access to all courses and materials</li>
            <li>May affect related submissions and grades</li>
          </ul>
        </Alert>
      </DialogContent>

      <DialogActions sx={{ p: 2, pt: 1 }}>
        <Button
          onClick={handleClose}
          disabled={loading}
          color="inherit"
        >
          Cancel
        </Button>
        <Button
          onClick={handleDelete}
          variant="contained"
          color="error"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : undefined}
        >
          {loading ? 'Deleting...' : 'Delete User'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteUserDialog;