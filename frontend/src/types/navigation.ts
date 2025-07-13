export interface NavigationItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  children?: NavigationItem[];
  permissions?: string[];
  context?: 'global' | 'course' | 'admin';
  badge?: {
    content: string | number;
    color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  };
}

export interface NavigationContext {
  type: 'global' | 'course' | 'admin';
  courseId?: string;
  courseName?: string;
  userPermissions: string[];
}

export interface SidebarConfig {
  collapsed: boolean;
  width: number;
  collapsedWidth: number;
  context: NavigationContext;
}

export type UserRole = 'student' | 'tutor' | 'lecturer' | 'admin' | 'owner';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  permissions: string[];
  courses?: string[];
}