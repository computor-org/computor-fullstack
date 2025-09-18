import React from 'react';
import {
  Avatar,
  Box,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Typography,
} from '@mui/material';
import { Logout, Settings } from '@mui/icons-material';
import { useSidebar } from '../../hooks/useSidebar';
import { useAuth } from '../../hooks/useAuth';

const AuthenticatedTopBarMenu: React.FC = () => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const { switchContext } = useSidebar();
  const { state: authState, logout } = useAuth();

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    await logout();
    handleClose();
  };

  const switchContextIfUserExists = (updater: () => void) => {
    if (authState.user) {
      updater();
    }
    handleClose();
  };

  if (!authState.user) {
    return null;
  }

  return (
    <>
      <IconButton size="small" color="inherit">
        <Settings />
      </IconButton>

      <IconButton size="large" onClick={handleMenu} color="inherit">
        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
          {authState.user.givenName.charAt(0)}
        </Avatar>
      </IconButton>

      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleClose}>
        <MenuItem disabled>
          <Box>
            <Typography variant="subtitle2">
              {authState.user.givenName} {authState.user.familyName}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {authState.user.email}
            </Typography>
          </Box>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() =>
            switchContextIfUserExists(() =>
              switchContext({
                type: 'global',
                userPermissions: authState.user?.permissions ?? [],
              })
            )
          }
        >
          Global View
        </MenuItem>
        <MenuItem
          onClick={() =>
            switchContextIfUserExists(() =>
              switchContext({
                type: 'course',
                courseId: '1',
                courseName: 'Introduction to Programming',
                userPermissions: authState.user?.permissions ?? [],
              })
            )
          }
        >
          Course: Intro Programming
        </MenuItem>
        {authState.user.permissions.includes('admin_access') && (
          <MenuItem
            onClick={() =>
              switchContextIfUserExists(() =>
                switchContext({
                  type: 'admin',
                  userPermissions: authState.user?.permissions ?? [],
                })
              )
            }
          >
            Administration
          </MenuItem>
        )}
        <Divider />
        <MenuItem onClick={handleLogout}>
          <Logout fontSize="small" sx={{ mr: 1 }} />
          Sign Out
        </MenuItem>
      </Menu>
    </>
  );
};

export default AuthenticatedTopBarMenu;
