import React from 'react';
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  LinearProgress,
} from '@mui/material';
import { mockCourses } from '../utils/mockData';

const CoursesPage: React.FC = () => {
  const getEnrollmentPercentage = (enrolled: number, max: number) => {
    return (enrolled / max) * 100;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'archived': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Courses
      </Typography>

      <Grid container spacing={3}>
        {mockCourses.map((course) => {
          const enrollmentPercentage = getEnrollmentPercentage(course.enrolledStudents, course.maxStudents);
          
          return (
            <Grid item xs={12} md={6} lg={4} key={course.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h2">
                      {course.title}
                    </Typography>
                    <Chip 
                      label={course.status} 
                      color={getStatusColor(course.status) as any}
                      size="small"
                    />
                  </Box>
                  
                  <Typography color="textSecondary" gutterBottom>
                    {course.code} • {course.semester}
                  </Typography>
                  
                  <Typography variant="body2" paragraph>
                    {course.description}
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      Instructor: {course.instructor}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Credits: {course.credits}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Enrollment: {course.enrolledStudents}/{course.maxStudents} ({enrollmentPercentage.toFixed(0)}%)
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={enrollmentPercentage}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                </CardContent>
                
                <CardActions>
                  <Button size="small" color="primary">
                    View Details
                  </Button>
                  <Button size="small" color="secondary">
                    Manage
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default CoursesPage;