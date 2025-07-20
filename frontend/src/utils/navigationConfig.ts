import { NavigationItem } from '../types/navigation';

export const globalNavigation: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: 'Dashboard',
    path: '/',
    context: 'global',
  },
  {
    id: 'courses',
    label: 'Courses',
    icon: 'School',
    path: '/courses',
    context: 'global',
    children: [
      {
        id: 'all-courses',
        label: 'All Courses',
        path: '/courses',
      },
      {
        id: 'my-courses',
        label: 'My Courses',
        path: '/courses/my',
      },
      {
        id: 'archived',
        label: 'Archived',
        path: '/courses/archived',
      },
    ],
  },
  {
    id: 'students',
    label: 'Students',
    icon: 'People',
    path: '/students',
    context: 'global',
    permissions: ['view_students'],
  },
  {
    id: 'assignments',
    label: 'Assignments',
    icon: 'Assignment',
    path: '/assignments',
    context: 'global',
  },
  {
    id: 'tasks',
    label: 'Tasks',
    icon: 'TaskAlt',
    path: '/tasks',
    context: 'global',
    permissions: ['admin_access'],
  },
  {
    id: 'admin',
    label: 'Administration',
    icon: 'AdminPanelSettings',
    context: 'admin',
    permissions: ['admin_access'],
    children: [
      {
        id: 'users',
        label: 'User Management',
        path: '/admin/users',
        permissions: ['manage_users'],
      },
      {
        id: 'system',
        label: 'System Settings',
        path: '/admin/system',
        permissions: ['system_settings'],
      },
      {
        id: 'audit',
        label: 'Audit Logs',
        path: '/admin/audit',
        permissions: ['view_audit'],
      },
    ],
  },
];

export const courseContextNavigation: NavigationItem[] = [
  {
    id: 'course-overview',
    label: 'Overview',
    icon: 'Info',
    path: '/course/:courseId',
    context: 'course',
  },
  {
    id: 'course-students',
    label: 'Students',
    icon: 'People',
    path: '/course/:courseId/students',
    context: 'course',
    permissions: ['view_course_students'],
    badge: {
      content: 45,
      color: 'primary',
    },
  },
  {
    id: 'course-assignments',
    label: 'Assignments',
    icon: 'Assignment',
    context: 'course',
    children: [
      {
        id: 'assignment-list',
        label: 'All Assignments',
        path: '/course/:courseId/assignments',
      },
      {
        id: 'create-assignment',
        label: 'Create Assignment',
        path: '/course/:courseId/assignments/new',
        permissions: ['create_assignments'],
      },
      {
        id: 'submissions',
        label: 'Submissions',
        path: '/course/:courseId/submissions',
        badge: {
          content: 12,
          color: 'warning',
        },
      },
    ],
  },
  {
    id: 'course-materials',
    label: 'Course Materials',
    icon: 'LibraryBooks',
    path: '/course/:courseId/materials',
    context: 'course',
  },
  {
    id: 'course-grades',
    label: 'Grades',
    icon: 'Grade',
    path: '/course/:courseId/grades',
    context: 'course',
    permissions: ['view_grades'],
  },
  {
    id: 'course-settings',
    label: 'Course Settings',
    icon: 'Settings',
    path: '/course/:courseId/settings',
    context: 'course',
    permissions: ['manage_course'],
  },
];

export const getNavigationForContext = (
  context: 'global' | 'course' | 'admin',
  userPermissions: string[],
  courseId?: string
): NavigationItem[] => {
  const baseNavigation = context === 'course' ? courseContextNavigation : globalNavigation;
  
  return filterNavigationByPermissions(baseNavigation, userPermissions).map(item => ({
    ...item,
    path: item.path?.replace(':courseId', courseId || ''),
    children: item.children?.map(child => ({
      ...child,
      path: child.path?.replace(':courseId', courseId || ''),
    })),
  }));
};

export const filterNavigationByPermissions = (
  navigation: NavigationItem[],
  userPermissions: string[]
): NavigationItem[] => {
  return navigation.filter(item => {
    // If no permissions required, show the item
    if (!item.permissions || item.permissions.length === 0) {
      return true;
    }
    
    // Check if user has any of the required permissions
    const hasPermission = item.permissions.some(permission => 
      userPermissions.includes(permission)
    );
    
    return hasPermission;
  }).map(item => ({
    ...item,
    children: item.children ? filterNavigationByPermissions(item.children, userPermissions) : undefined,
  }));
};