import React, { createContext, useContext, useState, ReactNode } from 'react';
import { SidebarConfig, NavigationContext, User } from '../types/navigation';
import { getNavigationForContext } from '../utils/navigationConfig';

interface SidebarContextType {
  config: SidebarConfig;
  updateConfig: (updates: Partial<SidebarConfig>) => void;
  switchContext: (context: NavigationContext) => void;
  currentNavigation: any[];
  contextInfo?: {
    title: string;
    subtitle?: string;
  };
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

interface SidebarProviderProps {
  children: ReactNode;
  user: User;
}

export const SidebarProvider: React.FC<SidebarProviderProps> = ({ children, user }) => {
  const [config, setConfig] = useState<SidebarConfig>({
    collapsed: false,
    width: 280,
    collapsedWidth: 64,
    context: {
      type: 'global',
      userPermissions: user.permissions,
    },
  });

  const updateConfig = (updates: Partial<SidebarConfig>) => {
    setConfig(prev => ({
      ...prev,
      ...updates,
      context: updates.context ? { ...prev.context, ...updates.context } : prev.context,
    }));
  };

  const switchContext = (context: NavigationContext) => {
    setConfig(prev => ({
      ...prev,
      context,
    }));
  };

  const currentNavigation = getNavigationForContext(
    config.context.type,
    config.context.userPermissions,
    config.context.courseId
  );

  const getContextInfo = () => {
    switch (config.context.type) {
      case 'course':
        return {
          title: config.context.courseName || 'Course',
          subtitle: 'Course Management',
        };
      case 'admin':
        return {
          title: 'Administration',
          subtitle: 'System Management',
        };
      default:
        return {
          title: 'Computor',
          subtitle: 'Course Management Platform',
        };
    }
  };

  const value: SidebarContextType = {
    config,
    updateConfig,
    switchContext,
    currentNavigation,
    contextInfo: getContextInfo(),
  };

  return (
    <SidebarContext.Provider value={value}>
      {children}
    </SidebarContext.Provider>
  );
};

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};