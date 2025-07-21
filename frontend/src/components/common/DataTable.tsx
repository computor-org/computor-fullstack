import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Box,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Toolbar,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Search as SearchIcon, Refresh as RefreshIcon } from '@mui/icons-material';

export interface Column<T> {
  id: string;
  label: string;
  accessor?: (row: T) => any;
  render?: (value: any, row: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  width?: string | number;
}

interface DataTableProps<T> {
  title: string;
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  error?: string | null;
  totalCount?: number;
  page: number;
  rowsPerPage: number;
  searchValue?: string;
  onPageChange: (newPage: number) => void;
  onRowsPerPageChange: (newRowsPerPage: number) => void;
  onSearchChange?: (search: string) => void;
  onRefresh?: () => void;
  actions?: React.ReactNode;
  rowActions?: (row: T) => React.ReactNode;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

export function DataTable<T extends { id: string }>({
  title,
  columns,
  data,
  loading = false,
  error = null,
  totalCount,
  page,
  rowsPerPage,
  searchValue = '',
  onPageChange,
  onRowsPerPageChange,
  onSearchChange,
  onRefresh,
  actions,
  rowActions,
  onRowClick,
  emptyMessage = 'No data available',
}: DataTableProps<T>) {
  const handleChangePage = (event: unknown, newPage: number) => {
    onPageChange(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    onRowsPerPageChange(parseInt(event.target.value, 10));
    onPageChange(0);
  };

  const displayedCount = totalCount !== undefined ? totalCount : data.length;

  return (
    <Paper sx={{ width: '100%', mb: 2 }}>
      <Toolbar sx={{ pl: { sm: 2 }, pr: { xs: 1, sm: 1 } }}>
        <Typography sx={{ flex: '1 1 100%' }} variant="h6" component="div">
          {title}
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {onSearchChange && (
            <TextField
              size="small"
              placeholder="Search..."
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 250 }}
            />
          )}
          
          {onRefresh && (
            <Tooltip title="Refresh">
              <IconButton onClick={onRefresh} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          )}
          
          {actions}
        </Box>
      </Toolbar>

      {error && (
        <Alert severity="error" sx={{ m: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align || 'left'}
                  style={{ width: column.width }}
                >
                  {column.label}
                </TableCell>
              ))}
              {rowActions && <TableCell align="right">Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={columns.length + (rowActions ? 1 : 0)} align="center">
                  <CircularProgress size={40} />
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length + (rowActions ? 1 : 0)} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                    {emptyMessage}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              data.map((row) => (
                <TableRow
                  key={row.id}
                  hover
                  onClick={() => onRowClick?.(row)}
                  sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                >
                  {columns.map((column) => {
                    const value = column.accessor ? column.accessor(row) : (row as any)[column.id];
                    return (
                      <TableCell key={column.id} align={column.align || 'left'}>
                        {column.render ? column.render(value, row) : value}
                      </TableCell>
                    );
                  })}
                  {rowActions && (
                    <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                      {rowActions(row)}
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[10, 25, 50, 100]}
        component="div"
        count={displayedCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
}