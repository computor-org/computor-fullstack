import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { 
  Box, 
  AppBar, 
  Toolbar, 
  Typography, 
  IconButton, 
  Avatar,
  Menu,
  MenuItem,
  Button,
  CircularProgress,
  Divider,
} from '@mui/material';
import { Settings, Login, Logout } from '@mui/icons-material';
import Dashboard from './pages/Dashboard';
import StudentsPage from './pages/StudentsPage';
import CoursesPage from './pages/CoursesPage';
import SSODebug from './pages/SSODebug';
import Tasks from './pages/Tasks';
import TaskDetail from './pages/TaskDetail';
import UsersPage from './pages/UsersPage';
import UserDetailPage from './pages/UserDetailPage';
import OrganizationsPage from './pages/OrganizationsPage';
import CourseFamiliesPage from './pages/CourseFamiliesPage';
import RolesPage from './pages/RolesPage';
import Sidebar from './components/Sidebar';
import SSOLoginModal from './components/SSOLoginModal';
import SSOCallback from './components/SSOCallback';
import { SidebarProvider, useSidebar } from './hooks/useSidebar';
import { AuthProvider, useAuth } from './hooks/useAuth';

function AuthenticatedTopBarMenu() {
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

  const switchToGlobal = () => {
    if (authState.user) {
      switchContext({
        type: 'global',
        userPermissions: authState.user.permissions,
      });
    }
    handleClose();
  };

  const switchToCourse = () => {
    if (authState.user) {
      switchContext({
        type: 'course',
        courseId: '1',
        courseName: 'Introduction to Programming',
        userPermissions: authState.user.permissions,
      });
    }
    handleClose();
  };

  const switchToAdmin = () => {
    if (authState.user) {
      switchContext({
        type: 'admin',
        userPermissions: authState.user.permissions,
      });
    }
    handleClose();
  };

  if (!authState.user) return null;

  return (
    <>
      <IconButton size="small" color="inherit">
        <Settings />
      </IconButton>
      
      <IconButton
        size="large"
        onClick={handleMenu}
        color="inherit"
      >
        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
          {authState.user.givenName.charAt(0)}
        </Avatar>
      </IconButton>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
      >
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
        <MenuItem onClick={switchToGlobal}>Global View</MenuItem>
        <MenuItem onClick={switchToCourse}>Course: Intro Programming</MenuItem>
        {authState.user.permissions.includes('admin_access') && (
          <MenuItem onClick={switchToAdmin}>Administration</MenuItem>
        )}
        <Divider />
        <MenuItem onClick={handleLogout}>
          <Logout fontSize="small" sx={{ mr: 1 }} />
          Sign Out
        </MenuItem>
      </Menu>
    </>
  );
}

function TopBar() {
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
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'primary.main', fontWeight: 600 }}>
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
      
      <SSOLoginModal
        open={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
      />
    </>
  );
}

function AuthenticatedAppContent() {
  const { config, updateConfig, currentNavigation, contextInfo } = useSidebar();
  const { state: authState } = useAuth();

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <TopBar />
      
      <Sidebar
        navigation={currentNavigation}
        config={config}
        onConfigChange={updateConfig}
        contextInfo={contextInfo}
      />
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 2,
          mt: 8, // Account for AppBar height
          transition: 'margin 0.3s ease',
          overflow: 'auto',
        }}
      >
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/admin/tasks" element={<Tasks />} />
          <Route path="/admin/tasks/:taskId" element={<TaskDetail />} />
          <Route path="/admin/users" element={<UsersPage />} />
          <Route path="/admin/users/:id" element={<UserDetailPage />} />
          <Route path="/admin/organizations" element={<OrganizationsPage />} />
          <Route path="/admin/course-families" element={<CourseFamiliesPage />} />
          <Route path="/admin/roles" element={<RolesPage />} />
          <Route path="/course/:courseId" element={<Dashboard />} />
          <Route path="/course/:courseId/students" element={<StudentsPage />} />
          <Route path="/admin/*" element={<Dashboard />} />
          <Route path="/debug/sso" element={<SSODebug />} />
        </Routes>
      </Box>
    </Box>
  );
}

function AppContent() {
  const { state: authState } = useAuth();

  if (authState.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress size={40} />
      </Box>
    );
  }

  if (!authState.isAuthenticated) {
    return (
      <Box sx={{ minHeight: '100vh' }}>
        <TopBar />
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: 'calc(100vh - 64px)',
            p: 3,
            textAlign: 'center',
          }}
        >
          <Typography variant="h4" gutterBottom>
            Welcome to Computor
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            University Programming Course Management Platform
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please sign in to access your courses and materials.
          </Typography>
        </Box>
      </Box>
    );
  }

  // User is authenticated, this will be handled by AuthenticatedSidebarProvider
  return null;
}

function AuthenticatedSidebarProvider() {
  const { state: authState } = useAuth();
  
  // Check if we're on an SSO callback route
  const isSSoCallback = window.location.pathname === '/auth/success' || 
                        window.location.pathname === '/auth/callback';
  
  if (isSSoCallback) {
    return <SSOCallback />;
  }
  
  if (!authState.isAuthenticated || !authState.user) {
    return <AppContent />;
  }

  return (
    <SidebarProvider user={authState.user}>
      <AuthenticatedAppContent />
    </SidebarProvider>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AuthenticatedSidebarProvider />
      </AuthProvider>
    </Router>
  );
}

export default App;