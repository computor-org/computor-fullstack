import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  IconButton,
  Box,
  Typography,
  Chip,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  ExpandLess,
  ExpandMore,
  ChevronLeft,
  ChevronRight,
  Dashboard,
  School,
  People,
  Assignment,
  AdminPanelSettings,
  Info,
  LibraryBooks,
  Grade,
  Settings,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { NavigationItem, SidebarConfig } from '../types/navigation';

// Icon mapping
const iconMap: { [key: string]: React.ComponentType } = {
  Dashboard,
  School,
  People,
  Assignment,
  AdminPanelSettings,
  Info,
  LibraryBooks,
  Grade,
  Settings,
};

interface SidebarProps {
  navigation: NavigationItem[];
  config: SidebarConfig;
  onConfigChange: (config: Partial<SidebarConfig>) => void;
  contextInfo?: {
    title: string;
    subtitle?: string;
  };
}

interface NavigationItemProps {
  item: NavigationItem;
  level: number;
  collapsed: boolean;
  onNavigate: (path: string) => void;
  currentPath: string;
}

const NavigationItemComponent: React.FC<NavigationItemProps> = ({
  item,
  level,
  collapsed,
  onNavigate,
  currentPath,
}) => {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = item.children && item.children.length > 0;
  const isActive = currentPath === item.path;
  const IconComponent = item.icon ? iconMap[item.icon] : null;

  const handleClick = () => {
    if (hasChildren) {
      setExpanded(!expanded);
    } else if (item.path) {
      onNavigate(item.path);
    }
  };

  const itemContent = (
    <ListItemButton
      selected={isActive}
      onClick={handleClick}
      sx={{
        pl: level * 2 + 1,
        borderRadius: 1,
        mx: 0.5,
        mb: 0.5,
        '&.Mui-selected': {
          backgroundColor: 'primary.main',
          color: 'primary.contrastText',
          '&:hover': {
            backgroundColor: 'primary.dark',
          },
        },
      }}
    >
      {IconComponent && (
        <ListItemIcon
          sx={{
            minWidth: collapsed ? 0 : 40,
            color: isActive ? 'inherit' : 'text.secondary',
          }}
        >
          <IconComponent />
        </ListItemIcon>
      )}
      
      {!collapsed && (
        <>
          <ListItemText 
            primary={item.label}
            sx={{ 
              '& .MuiListItemText-primary': {
                fontSize: level === 0 ? '0.9rem' : '0.85rem',
                fontWeight: level === 0 ? 500 : 400,
              },
            }}
          />
          
          {item.badge && (
            <Chip
              label={item.badge.content}
              size="small"
              color={item.badge.color || 'default'}
              sx={{ ml: 1, minWidth: 20, height: 20 }}
            />
          )}
          
          {hasChildren && (expanded ? <ExpandLess /> : <ExpandMore />)}
        </>
      )}
    </ListItemButton>
  );

  return (
    <>
      {collapsed && item.label ? (
        <Tooltip title={item.label} placement="right">
          <ListItem disablePadding>
            {itemContent}
          </ListItem>
        </Tooltip>
      ) : (
        <ListItem disablePadding>
          {itemContent}
        </ListItem>
      )}
      
      {hasChildren && !collapsed && (
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {item.children?.map((child) => (
              <NavigationItemComponent
                key={child.id}
                item={child}
                level={level + 1}
                collapsed={collapsed}
                onNavigate={onNavigate}
                currentPath={currentPath}
              />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
};

const Sidebar: React.FC<SidebarProps> = ({
  navigation,
  config,
  onConfigChange,
  contextInfo,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  const toggleCollapsed = () => {
    onConfigChange({ collapsed: !config.collapsed });
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: config.collapsed ? config.collapsedWidth : config.width,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: config.collapsed ? config.collapsedWidth : config.width,
          boxSizing: 'border-box',
          borderRight: '1px solid',
          borderColor: 'divider',
          transition: 'width 0.3s ease',
          overflowX: 'hidden',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 1,
          minHeight: 64,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        {!config.collapsed && contextInfo && (
          <Box sx={{ flexGrow: 1, ml: 1 }}>
            <Typography variant="subtitle2" noWrap>
              {contextInfo.title}
            </Typography>
            {contextInfo.subtitle && (
              <Typography variant="caption" color="text.secondary" noWrap>
                {contextInfo.subtitle}
              </Typography>
            )}
          </Box>
        )}
        
        <IconButton onClick={toggleCollapsed} size="small">
          {config.collapsed ? <ChevronRight /> : <ChevronLeft />}
        </IconButton>
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 1 }}>
        <List>
          {navigation.map((item, index) => (
            <React.Fragment key={item.id}>
              <NavigationItemComponent
                item={item}
                level={0}
                collapsed={config.collapsed}
                onNavigate={handleNavigate}
                currentPath={location.pathname}
              />
              {index < navigation.length - 1 && item.context === 'admin' && (
                <Divider sx={{ my: 1 }} />
              )}
            </React.Fragment>
          ))}
        </List>
      </Box>
    </Drawer>
  );
};

export default Sidebar;