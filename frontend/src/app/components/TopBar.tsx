import React, { useState } from 'react';
import {
  AppBar,
  Box,
  Button,
  CircularProgress,
  Toolbar,
  Typography,
} from '@mui/material';
import { Login } from '@mui/icons-material';
import AuthenticatedTopBarMenu from './AuthenticatedTopBarMenu';
import SSOLoginModal from '../../components/SSOLoginModal';
import { useAuth } from '../../hooks/useAuth';

const TopBar: React.FC = () => {
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const { state: authState } = useAuth();

  const handleLogin = () => {
    setLoginModalOpen(true);
  };

  return (
    <>
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: 'white',
          color: 'text.primary',
          boxShadow: 1,
        }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, color: 'primary.main', fontWeight: 600 }}
          >
            Computor
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {authState.isLoading ? (
              <CircularProgress size={24} />
            ) : authState.isAuthenticated && authState.user ? (
              <AuthenticatedTopBarMenu />
            ) : (
              <Button
                variant="contained"
                startIcon={<Login />}
                onClick={handleLogin}
                size="small"
              >
                Sign In
              </Button>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      <SSOLoginModal open={loginModalOpen} onClose={() => setLoginModalOpen(false)} />
    </>
  );
};

export default TopBar;
