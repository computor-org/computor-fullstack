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
  Grid,
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
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Business as BusinessIcon,
  AccountTree as AccountTreeIcon,
  Code as CodeIcon,
  CalendarToday as CalendarTodayIcon,
  Person as PersonIcon,
  MoveDown as MoveDownIcon,
  CloudUpload as CloudUploadIcon,
  Publish as PublishIcon,
} from '@mui/icons-material';
import { CourseGet, CourseContentGet, CourseContentTypeGet, CourseContentKindGet } from '../types/generated/courses';
import { apiClient } from '../services/apiClient';
import AddCourseContentDialog from '../components/AddCourseContentDialog';
import ManageCourseContentTypesDialog from '../components/ManageCourseContentTypesDialog';
import EditCourseContentDialog from '../components/EditCourseContentDialog';
import DeleteCourseContentDialog from '../components/DeleteCourseContentDialog';
import MoveCourseContentDialog from '../components/MoveCourseContentDialog';
import DeployExampleDialog from '../components/DeployExampleDialog';
import DeploymentStatusChip from '../components/DeploymentStatusChip';

const CourseDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [course, setCourse] = useState<CourseGet | null>(null);
  const [courseContent, setCourseContent] = useState<CourseContentGet[]>([]);
  const [contentTypes, setContentTypes] = useState<CourseContentTypeGet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addContentOpen, setAddContentOpen] = useState(false);
  const [manageTypesOpen, setManageTypesOpen] = useState(false);
  const [editContentOpen, setEditContentOpen] = useState(false);
  const [deleteContentOpen, setDeleteContentOpen] = useState(false);
  const [moveContentOpen, setMoveContentOpen] = useState(false);
  const [deployExampleOpen, setDeployExampleOpen] = useState(false);
  const [selectedContent, setSelectedContent] = useState<CourseContentGet | null>(null);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  const [contentKinds, setContentKinds] = useState<CourseContentKindGet[]>([]);

  // Load course details
  const loadCourseContent = async () => {
    if (!id) return;
    
    try {
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
      console.error('Error loading course content:', err);
    }
  };

  const loadCourse = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Load course details
      const courseData = await apiClient.get<CourseGet>(`/courses/${id}`);
      setCourse(courseData);
      
      // Load course content
      await loadCourseContent();
      
      // Load content types and kinds
      await loadContentTypes();
      await loadContentKinds();
      
    } catch (err: any) {
      console.error('Error loading course:', err);
      setError(err.message || 'Failed to load course');
    } finally {
      setLoading(false);
    }
  };

  const loadContentTypes = async () => {
    if (!id) return;
    
    try {
      const response = await apiClient.get<CourseContentTypeGet[]>('/course-content-types', {
        params: {
          course_id: id,
          limit: 100,
        },
      });
      const data = Array.isArray(response) ? response : (response as any).data || [];
      setContentTypes(data);
    } catch (err) {
      console.error('Error loading content types:', err);
    }
  };

  const loadContentKinds = async () => {
    try {
      const response = await apiClient.get<CourseContentKindGet[]>('/course-content-kinds', {
        params: {
          limit: 100,
        },
      });
      const data = Array.isArray(response) ? response : (response as any).data || [];
      setContentKinds(data);
    } catch (err) {
      console.error('Error loading content kinds:', err);
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

  const hasChildren = (item: CourseContentGet) => {
    return courseContent.some(content => 
      content.path.startsWith(item.path + '.') && 
      content.path.split('.').length === item.path.split('.').length + 1
    );
  };

  const handleGenerateStudentTemplate = async () => {
    if (!course) return;
    
    try {
      const response = await apiClient.post(`/system/courses/${course.id}/generate-student-template`, {
        commit_message: `Update student template - ${new Date().toLocaleDateString()}`
      });
      
      // Show success message
      alert('Student template generation started! Check the workflow status for progress.');
      
      // Reload course content to update deployment status
      await loadCourseContent();
    } catch (err: any) {
      console.error('Error generating student template:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate student template';
      
      // Check for specific error about missing GitLab configuration
      if (errorMessage.includes('GitLab') || errorMessage.includes('student-template')) {
        // Fetch GitLab status for more info
        try {
          const status = await apiClient.get<{
            course_id: string;
            has_gitlab_config: boolean;
            has_student_template_url: boolean;
            recommendations: string[];
            missing_items: string[];
          }>(`/system/courses/${course.id}/gitlab-status`);
          console.log('GitLab status:', status);
          
          let message = `Cannot generate template: ${errorMessage}\n\n`;
          if (status.recommendations && status.recommendations.length > 0) {
            message += `Recommendations:\n${status.recommendations.join('\n')}`;
          }
          alert(message);
        } catch {
          alert(`Cannot generate template: ${errorMessage}\n\nMake sure the course has GitLab integration enabled and repositories created.`);
        }
      } else {
        alert(`Error: ${errorMessage}`);
      }
    }
  };

  const toggleExpand = (path: string) => {
    const newExpanded = new Set(expandedPaths);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedPaths(newExpanded);
  };

  const renderContentItem = (item: CourseContentGet, level: number = 0) => {
    const pathParts = item.path.split('.');
    const isChild = pathParts.length > 1;
    const hasChildContent = hasChildren(item);
    const isExpanded = expandedPaths.has(item.path);
    
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
          },
        }}
      >
        {/* Expand/Collapse button */}
        <Box sx={{ width: 30, mr: 1 }}>
          {hasChildContent && (
            <IconButton
              size="small"
              onClick={() => toggleExpand(item.path)}
              sx={{ p: 0.5 }}
            >
              {isExpanded ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
            </IconButton>
          )}
        </Box>

        <Box 
          sx={{ 
            mr: 2, 
            color: item.course_content_type?.color || 'action.active',
            cursor: 'pointer',
            position: 'relative',
          }}
          onClick={() => {/* TODO: Navigate to content detail */}}
        >
          {getContentIcon(item.course_content_kind_id)}
          {/* Show a small badge if example is assigned */}
          {item.example_id && (
            <Box
              sx={{
                position: 'absolute',
                top: -4,
                right: -4,
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: item.deployment_status === 'released' ? 'success.main' : 'warning.main',
                border: '1px solid',
                borderColor: 'background.paper',
              }}
            />
          )}
        </Box>
        <Box sx={{ flexGrow: 1, cursor: 'pointer' }} onClick={() => {/* TODO: Navigate to content detail */}}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <Typography variant="body1">
              {item.title || pathParts[pathParts.length - 1]}
            </Typography>
            {/* Show example name if assigned */}
            {item.example_id && (
              <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                (has example)
              </Typography>
            )}
          </Stack>
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
              mr: 1,
            }}
          />
        )}
        {/* Show deployment status if example is deployed */}
        {item.example_id && course && (
          <DeploymentStatusChip
            courseId={course.id}
            deploymentStatus={item.deployment_status}
            exampleVersion={item.example_version}
          />
        )}
        {/* Only show deploy button for assignment type content */}
        {item.course_content_kind_id === 'assignment' && (
          <IconButton 
            size="small" 
            sx={{ ml: 1 }}
            onClick={(e) => {
              e.stopPropagation();
              setSelectedContent(item);
              setDeployExampleOpen(true);
            }}
            title="Deploy Example"
            color="primary"
          >
            <CloudUploadIcon fontSize="small" />
          </IconButton>
        )}
        <IconButton 
          size="small" 
          sx={{ ml: 1 }}
          onClick={(e) => {
            e.stopPropagation();
            setSelectedContent(item);
            setEditContentOpen(true);
          }}
          title="Edit"
        >
          <EditIcon fontSize="small" />
        </IconButton>
        <IconButton 
          size="small" 
          sx={{ ml: 0.5 }}
          onClick={(e) => {
            e.stopPropagation();
            setSelectedContent(item);
            setMoveContentOpen(true);
          }}
          title="Move"
        >
          <MoveDownIcon fontSize="small" />
        </IconButton>
        <IconButton 
          size="small" 
          sx={{ ml: 0.5 }}
          color="error"
          onClick={(e) => {
            e.stopPropagation();
            setSelectedContent(item);
            setDeleteContentOpen(true);
          }}
          title="Delete"
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      </Box>
    );
  };

  // Build hierarchy from flat list
  const buildHierarchy = (items: CourseContentGet[]) => {
    const hierarchy: React.ReactElement[] = [];
    
    // Recursive function to render an item and its children
    const renderItemAndChildren = (item: CourseContentGet, level: number = 0): void => {
      // Render the current item
      hierarchy.push(renderContentItem(item, level));
      
      // If this item is expanded, render its immediate children
      if (expandedPaths.has(item.path)) {
        const children = items
          .filter(child => {
            const childParts = child.path.split('.');
            const itemParts = item.path.split('.');
            // Check if this is a direct child (one level deeper and starts with parent path)
            return childParts.length === itemParts.length + 1 && 
                   child.path.startsWith(item.path + '.');
          })
          .sort((a, b) => a.position - b.position); // Sort children by position
        
        children.forEach(child => {
          renderItemAndChildren(child, level + 1);
        });
      }
    };
    
    // Start with root items (no dots in path)
    const rootItems = items
      .filter(item => !item.path.includes('.'))
      .sort((a, b) => a.position - b.position);
    
    rootItems.forEach(item => {
      renderItemAndChildren(item, 0);
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

      {/* Course Info Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {/* Main Course Info */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Course Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Stack spacing={2}>
                <Box>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                    <AccountTreeIcon fontSize="small" color="action" />
                    <Typography variant="subtitle2" color="text.secondary">
                      Path
                    </Typography>
                  </Stack>
                  <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                    {course.path}
                  </Typography>
                </Box>
                
                {course.description && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Description
                    </Typography>
                    <Typography variant="body1">{course.description}</Typography>
                  </Box>
                )}
                
                {course.version_identifier && (
                  <Box>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                      <CodeIcon fontSize="small" color="action" />
                      <Typography variant="subtitle2" color="text.secondary">
                        Version
                      </Typography>
                    </Stack>
                    <Typography variant="body1">{course.version_identifier}</Typography>
                  </Box>
                )}
                
                <Box>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Technical Details
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                    {course.properties?.gitlab?.group_id && (
                      <Chip
                        label={`GitLab Group: ${course.properties.gitlab.group_id}`}
                        size="small"
                        color="success"
                        variant="outlined"
                        icon={<CodeIcon />}
                      />
                    )}
                    <Chip
                      label={`ID: ${course.id}`}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Organization & Course Family Info */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Hierarchy
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Stack spacing={3}>
                {/* Organization */}
                {course.course_family?.organization && (
                  <Box>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                      <BusinessIcon fontSize="small" color="primary" />
                      <Typography variant="subtitle2" color="text.secondary">
                        Organization
                      </Typography>
                    </Stack>
                    <Typography variant="body1" fontWeight="medium">
                      {course.course_family.organization.title || course.course_family.organization.path}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {course.course_family.organization.path}
                    </Typography>
                  </Box>
                )}
                
                {/* Course Family */}
                {course.course_family && (
                  <Box>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                      <SchoolIcon fontSize="small" color="primary" />
                      <Typography variant="subtitle2" color="text.secondary">
                        Course Family
                      </Typography>
                    </Stack>
                    <Typography variant="body1" fontWeight="medium">
                      {course.course_family.title || course.course_family.path}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {course.course_family.path}
                    </Typography>
                  </Box>
                )}
                
                {/* Timestamps */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Metadata
                  </Typography>
                  <Stack spacing={1}>
                    {course.created_at && (
                      <Stack direction="row" spacing={1} alignItems="center">
                        <CalendarTodayIcon fontSize="small" color="action" />
                        <Typography variant="caption" color="text.secondary">
                          Created: {new Date(course.created_at).toLocaleDateString()}
                        </Typography>
                      </Stack>
                    )}
                    {course.updated_at && (
                      <Stack direction="row" spacing={1} alignItems="center">
                        <CalendarTodayIcon fontSize="small" color="action" />
                        <Typography variant="caption" color="text.secondary">
                          Updated: {new Date(course.updated_at).toLocaleDateString()}
                        </Typography>
                      </Stack>
                    )}
                    {course.created_by && (
                      <Stack direction="row" spacing={1} alignItems="center">
                        <PersonIcon fontSize="small" color="action" />
                        <Typography variant="caption" color="text.secondary">
                          Created by: {course.created_by}
                        </Typography>
                      </Stack>
                    )}
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Course Content Section */}
      <Paper sx={{ p: 3 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h5">Course Content</Typography>
            {/* Show summary of assigned examples */}
            {courseContent.filter(c => c.example_id).length > 0 && (
              <Typography variant="caption" color="text.secondary">
                {courseContent.filter(c => c.example_id).length} example{courseContent.filter(c => c.example_id).length !== 1 ? 's' : ''} assigned
                {courseContent.filter(c => c.deployment_status === 'pending_release').length > 0 && (
                  <> • {courseContent.filter(c => c.deployment_status === 'pending_release').length} pending release</>
                )}
              </Typography>
            )}
          </Box>
          <Stack direction="row" spacing={1}>
            {courseContent.length > 0 && (
              <Button
                variant="text"
                size="small"
                onClick={() => {
                  if (expandedPaths.size > 0) {
                    setExpandedPaths(new Set());
                  } else {
                    // Expand all parent nodes
                    const allParentPaths = new Set<string>();
                    courseContent.forEach(item => {
                      if (hasChildren(item)) {
                        allParentPaths.add(item.path);
                      }
                    });
                    setExpandedPaths(allParentPaths);
                  }
                }}
              >
                {expandedPaths.size > 0 ? 'Collapse All' : 'Expand All'}
              </Button>
            )}
            <Button
              variant="outlined"
              onClick={() => setManageTypesOpen(true)}
            >
              Manage Types
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setAddContentOpen(true)}
            >
              Add Content
            </Button>
            {/* Always show Generate Student Template button */}
            <Button
              variant="contained"
              color="secondary"
              startIcon={<PublishIcon />}
              onClick={handleGenerateStudentTemplate}
            >
              Generate Student Template
            </Button>
          </Stack>
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

      {/* Manage Content Types Dialog */}
      {course && (
        <ManageCourseContentTypesDialog
          open={manageTypesOpen}
          onClose={() => setManageTypesOpen(false)}
          courseId={course.id}
          onTypesChanged={() => {
            // This will trigger refresh in AddCourseContentDialog
            loadContentTypes();
          }}
        />
      )}

      {/* Edit Content Dialog */}
      {course && selectedContent && (
        <EditCourseContentDialog
          open={editContentOpen}
          onClose={() => {
            setEditContentOpen(false);
            setSelectedContent(null);
          }}
          content={selectedContent}
          contentTypes={contentTypes}
          onContentUpdated={() => {
            setEditContentOpen(false);
            setSelectedContent(null);
            loadCourse();
          }}
        />
      )}

      {/* Delete Content Dialog */}
      {course && selectedContent && (
        <DeleteCourseContentDialog
          open={deleteContentOpen}
          onClose={() => {
            setDeleteContentOpen(false);
            setSelectedContent(null);
          }}
          content={selectedContent}
          allContent={courseContent}
          onContentDeleted={() => {
            setDeleteContentOpen(false);
            setSelectedContent(null);
            loadCourse();
          }}
        />
      )}

      {/* Move Content Dialog */}
      {course && selectedContent && (
        <MoveCourseContentDialog
          open={moveContentOpen}
          onClose={() => {
            setMoveContentOpen(false);
            setSelectedContent(null);
          }}
          content={selectedContent}
          allContent={courseContent}
          contentTypes={contentTypes}
          contentKinds={contentKinds}
          onContentMoved={() => {
            setMoveContentOpen(false);
            setSelectedContent(null);
            loadCourse();
          }}
        />
      )}

      {/* Deploy Example Dialog */}
      {course && selectedContent && (
        <DeployExampleDialog
          open={deployExampleOpen}
          onClose={() => {
            setDeployExampleOpen(false);
            setSelectedContent(null);
          }}
          courseId={course.id}
          content={selectedContent}
          onDeploymentStarted={() => {
            setDeployExampleOpen(false);
            setSelectedContent(null);
            loadCourse();
          }}
        />
      )}
    </Box>
  );
};

export default CourseDetailPage;