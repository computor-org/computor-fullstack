import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Stack,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  IconButton,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Folder as FolderIcon,
  Assignment as AssignmentIcon,
  Quiz as QuizIcon,
  MenuBook as MenuBookIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import { CourseGet, CourseContentGet } from '../types/generated/courses';
import { apiClient } from '../services/apiClient';
import AddCourseContentDialog from '../components/AddCourseContentDialog';

const CourseDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [course, setCourse] = useState<CourseGet | null>(null);
  const [courseContent, setCourseContent] = useState<CourseContentGet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addContentOpen, setAddContentOpen] = useState(false);

  // Load course details
  const loadCourse = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Load course details
      const courseData = await apiClient.get<CourseGet>(`/courses/${id}`);
      setCourse(courseData);
      
      // Load course content
      const contentResponse = await apiClient.get<CourseContentGet[]>('/course-contents', {
        params: {
          course_id: id,
          limit: 100,
        },
      });
      const contentData = Array.isArray(contentResponse) ? contentResponse : (contentResponse as any).data || [];
      
      // Sort by path to ensure hierarchical order
      const sortedContent = contentData.sort((a: CourseContentGet, b: CourseContentGet) => {
        // First sort by path depth (parents before children)
        const depthA = a.path.split('.').length;
        const depthB = b.path.split('.').length;
        if (depthA !== depthB) return depthA - depthB;
        
        // Then sort by position within same level
        return a.position - b.position;
      });
      
      setCourseContent(sortedContent);
      
    } catch (err: any) {
      console.error('Error loading course:', err);
      setError(err.message || 'Failed to load course');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourse();
  }, [id]);

  const getContentIcon = (kind: string) => {
    switch (kind) {
      case 'unit':
        return <SchoolIcon fontSize="small" />;
      case 'folder':
        return <FolderIcon fontSize="small" />;
      case 'assignment':
        return <AssignmentIcon fontSize="small" />;
      case 'quiz':
        return <QuizIcon fontSize="small" />;
      case 'reading':
      case 'lecture':
        return <MenuBookIcon fontSize="small" />;
      default:
        return <FolderIcon fontSize="small" />;
    }
  };

  const renderContentItem = (item: CourseContentGet, level: number = 0) => {
    const pathParts = item.path.split('.');
    const isChild = pathParts.length > 1;
    
    return (
      <Box
        key={item.id}
        sx={{
          display: 'flex',
          alignItems: 'center',
          py: 1.5,
          px: 2,
          ml: level * 4,
          borderRadius: 1,
          '&:hover': {
            backgroundColor: 'action.hover',
            cursor: 'pointer',
          },
        }}
      >
        <Box sx={{ mr: 2, color: item.course_content_type?.color || 'action.active' }}>
          {getContentIcon(item.course_content_kind_id)}
        </Box>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="body1">
            {item.title || pathParts[pathParts.length - 1]}
          </Typography>
          {item.description && (
            <Typography variant="body2" color="text.secondary">
              {item.description}
            </Typography>
          )}
        </Box>
        {item.course_content_type && (
          <Chip
            label={item.course_content_type.title}
            size="small"
            sx={{
              backgroundColor: item.course_content_type.color || 'action.selected',
              color: 'white',
            }}
          />
        )}
        <IconButton size="small" sx={{ ml: 1 }}>
          <EditIcon fontSize="small" />
        </IconButton>
      </Box>
    );
  };

  // Build hierarchy from flat list
  const buildHierarchy = (items: CourseContentGet[]) => {
    const hierarchy: React.ReactElement[] = [];
    const processedPaths = new Set<string>();
    
    items.forEach((item) => {
      if (!processedPaths.has(item.path)) {
        const level = item.path.split('.').length - 1;
        hierarchy.push(renderContentItem(item, level));
        processedPaths.add(item.path);
      }
    });
    
    return hierarchy;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Box>
    );
  }

  if (!course) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">Course not found</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
        <IconButton onClick={() => navigate('/admin/courses')}>
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" gutterBottom>
            {course.title || 'Untitled Course'}
          </Typography>
          <Breadcrumbs>
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/admin/organizations')}
              sx={{ cursor: 'pointer' }}
            >
              Organizations
            </Link>
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/admin/course-families')}
              sx={{ cursor: 'pointer' }}
            >
              Course Families
            </Link>
            <Typography color="text.primary" variant="body2">
              {course.title}
            </Typography>
          </Breadcrumbs>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/admin/courses/${id}/edit`)}
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
          >
            Delete
          </Button>
        </Stack>
      </Stack>

      {/* Course Info Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Path
              </Typography>
              <Typography variant="body1">{course.path}</Typography>
            </Box>
            
            {course.description && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Description
                </Typography>
                <Typography variant="body1">{course.description}</Typography>
              </Box>
            )}
            
            <Box>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Details
              </Typography>
              <Stack direction="row" spacing={2} flexWrap="wrap">
                <Chip
                  label={`Course Family: ${course.course_family_id}`}
                  size="small"
                  icon={<SchoolIcon />}
                />
                {course.properties?.gitlab?.group_id && (
                  <Chip
                    label="GitLab Enabled"
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                )}
              </Stack>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* Course Content Section */}
      <Paper sx={{ p: 3 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h5">Course Content</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddContentOpen(true)}
          >
            Add Content
          </Button>
        </Stack>
        
        <Divider sx={{ mb: 2 }} />
        
        {courseContent.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              No content added yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Click "Add Content" to start building your course structure
            </Typography>
          </Box>
        ) : (
          <Box>
            {buildHierarchy(courseContent)}
          </Box>
        )}
      </Paper>

      {/* Add Content Dialog */}
      {course && (
        <AddCourseContentDialog
          open={addContentOpen}
          onClose={() => setAddContentOpen(false)}
          courseId={course.id}
          existingContent={courseContent}
          onContentAdded={() => {
            setAddContentOpen(false);
            loadCourse();
          }}
        />
      )}
    </Box>
  );
};

export default CourseDetailPage;