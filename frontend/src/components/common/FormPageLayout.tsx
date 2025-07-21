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
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Fixed Header */}
      <Box
        sx={{
          flexShrink: 0,
          bgcolor: 'background.default',
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        {/* Title Section */}
        <Box sx={{ p: 3, pb: headerContent ? 1 : 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {onBack && (
              <IconButton onClick={onBack} edge="start">
                <ArrowBackIcon />
              </IconButton>
            )}
            <Box>
              <Typography variant="h4">{title}</Typography>
              {subtitle && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {subtitle}
                </Typography>
              )}
            </Box>
          </Box>
        </Box>

        {/* Optional Header Content (Progress bars, alerts, etc.) */}
        {headerContent && (
          <Box sx={{ px: 3, pb: 2 }}>
            {headerContent}
          </Box>
        )}
      </Box>

      {/* Scrollable Content Area */}
      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          bgcolor: 'background.default',
          p: 3,
        }}
      >
        <Paper
          sx={{
            p: 3,
            maxWidth,
            mx: 'auto',
            mb: 2, // Add margin bottom to ensure content doesn't get hidden behind footer
          }}
        >
          {children}
        </Paper>
      </Box>

      {/* Fixed Footer with Actions */}
      {actions && (
        <Box
          sx={{
            flexShrink: 0,
            bgcolor: 'background.paper',
            borderTop: 1,
            borderColor: 'divider',
            p: 3,
          }}
        >
          <Box sx={{ maxWidth, mx: 'auto' }}>
            {actions}
          </Box>
        </Box>
      )}
    </Box>
  );
};