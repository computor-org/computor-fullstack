import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  CircularProgress,
} from '@mui/material';

interface FormDialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  loading?: boolean;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  children: React.ReactNode;
}

export const FormDialog: React.FC<FormDialogProps> = ({
  open,
  onClose,
  title,
  loading = false,
  maxWidth = 'sm',
  children,
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth={maxWidth} fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>{children}</Box>
      </DialogContent>
    </Dialog>
  );
};