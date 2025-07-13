import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Box, Button } from '@mui/material';
import Dashboard from './pages/Dashboard';
import StudentsPage from './pages/StudentsPage';
import CoursesPage from './pages/CoursesPage';

function Navigation() {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;
  
  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <Button 
        color="inherit" 
        component={Link} 
        to="/"
        variant={isActive('/') ? 'outlined' : 'text'}
      >
        Dashboard
      </Button>
      <Button 
        color="inherit" 
        component={Link} 
        to="/students"
        variant={isActive('/students') ? 'outlined' : 'text'}
      >
        Students
      </Button>
      <Button 
        color="inherit" 
        component={Link} 
        to="/courses"
        variant={isActive('/courses') ? 'outlined' : 'text'}
      >
        Courses
      </Button>
    </Box>
  );
}

function App() {
  return (
    <Router>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Computor Frontend
            </Typography>
            <Navigation />
          </Toolbar>
        </AppBar>
        
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/students" element={<StudentsPage />} />
            <Route path="/courses" element={<CoursesPage />} />
          </Routes>
        </Container>
      </Box>
    </Router>
  );
}

export default App;