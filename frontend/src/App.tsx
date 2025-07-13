import React from 'react';
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
} from '@mui/material';
import { Settings, AccountCircle } from '@mui/icons-material';
import Dashboard from './pages/Dashboard';
import StudentsPage from './pages/StudentsPage';
import CoursesPage from './pages/CoursesPage';
import Sidebar from './components/Sidebar';
import { SidebarProvider, useSidebar } from './hooks/useSidebar';
import { mockUser } from './utils/mockData';

function TopBar() {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const { switchContext, config } = useSidebar();

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const switchToGlobal = () => {
    switchContext({
      type: 'global',
      userPermissions: mockUser.permissions,
    });
    handleClose();
  };

  const switchToCourse = () => {
    switchContext({
      type: 'course',
      courseId: '1',
      courseName: 'Introduction to Programming',
      userPermissions: mockUser.permissions,
    });
    handleClose();
  };

  const switchToAdmin = () => {
    switchContext({
      type: 'admin',
      userPermissions: mockUser.permissions,
    });
    handleClose();
  };

  return (
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
          <IconButton size="small" color="inherit">
            <Settings />
          </IconButton>
          
          <IconButton
            size="large"
            onClick={handleMenu}
            color="inherit"
          >
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
              {mockUser.name.charAt(0)}
            </Avatar>
          </IconButton>
          
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={switchToGlobal}>Global View</MenuItem>
            <MenuItem onClick={switchToCourse}>Course: Intro Programming</MenuItem>
            <MenuItem onClick={switchToAdmin}>Administration</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

function AppContent() {
  const { config, updateConfig, currentNavigation, contextInfo } = useSidebar();

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
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/course/:courseId" element={<Dashboard />} />
          <Route path="/course/:courseId/students" element={<StudentsPage />} />
          <Route path="/admin/*" element={<Dashboard />} />
        </Routes>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <Router>
      <SidebarProvider user={mockUser}>
        <AppContent />
      </SidebarProvider>
    </Router>
  );
}

export default App;