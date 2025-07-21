import React from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Divider,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';

interface FormPageLayoutProps {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  headerContent?: React.ReactNode;
  children: React.ReactNode;
  actions?: React.ReactNode;
  maxWidth?: number | string;
}

/**
 * Reusable layout component for form pages with fixed header/footer and scrollable content.
 * 
 * Features:
 * - Fixed header with title and back button
 * - Optional header content (e.g., progress bars, alerts)
 * - Scrollable main content area
 * - Fixed footer with action buttons
 */
export const FormPageLayout: React.FC<FormPageLayoutProps> = ({
  title,
  subtitle,
  onBack,
  headerContent,
  children,
  actions,
  maxWidth = 1000,
}) => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      {/* Header */}
      <Box sx={{ pl: 3, pr: 3, pt: 3, pb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          {onBack && (
            <IconButton onClick={onBack} edge="start">
              <ArrowBackIcon />
            </IconButton>
          )}
          <Typography variant="h4" component="h1">
            {title}
          </Typography>
        </Box>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" sx={{ ml: onBack ? 7 : 0, mb: 2 }}>
            {subtitle}
          </Typography>
        )}
        {headerContent && (
          <Box sx={{ mt: 2 }}>
            {headerContent}
          </Box>
        )}
      </Box>

      {/* Content Area */}
      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          px: 3,
          pb: actions ? 10 : 3, // Add padding bottom if actions exist
        }}
      >
        <Paper
          sx={{
            p: 3,
            maxWidth,
            mx: 'auto',
          }}
        >
          {children}
        </Paper>
      </Box>

      {/* Fixed Footer with Actions */}
      {actions && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            borderTop: 1,
            borderColor: 'divider',
            bgcolor: 'background.paper',
            px: 3,
            py: 2,
          }}
        >
          <Box 
            sx={{ 
              display: 'flex',
              justifyContent: 'flex-end',
            }}
          >
            {actions}
          </Box>
        </Box>
      )}
    </Box>
  );
};