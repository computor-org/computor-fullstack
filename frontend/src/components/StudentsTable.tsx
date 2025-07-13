import React, { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  ColumnDef,
  flexRender,
  ColumnFiltersState,
  SortingState,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  Box,
  Button,
  Chip,
  TablePagination,
  IconButton,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { Student } from '../types';

interface StudentsTableProps {
  data: Student[];
  onEdit?: (student: Student) => void;
  onDelete?: (studentId: string) => void;
}

const StudentsTable: React.FC<StudentsTableProps> = ({ data, onEdit, onDelete }) => {
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const columns = useMemo<ColumnDef<Student>[]>(
    () => [
      {
        accessorKey: 'studentId',
        header: 'Student ID',
        cell: ({ getValue }) => (
          <strong>{getValue<string>()}</strong>
        ),
      },
      {
        accessorKey: 'givenName',
        header: 'First Name',
      },
      {
        accessorKey: 'familyName',
        header: 'Last Name',
      },
      {
        accessorKey: 'email',
        header: 'Email',
      },
      {
        accessorKey: 'enrollmentDate',
        header: 'Enrollment Date',
        cell: ({ getValue }) => {
          const date = new Date(getValue<string>());
          return date.toLocaleDateString();
        },
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ getValue }) => {
          const status = getValue<string>();
          const color = status === 'active' ? 'success' : status === 'inactive' ? 'default' : 'error';
          return <Chip label={status} color={color} size="small" />;
        },
      },
      {
        accessorKey: 'grade',
        header: 'Grade',
        cell: ({ getValue }) => {
          const grade = getValue<number>();
          return grade ? `${grade}%` : 'N/A';
        },
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <Box>
            <IconButton
              size="small"
              onClick={() => onEdit?.(row.original)}
              color="primary"
            >
              <EditIcon />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => onDelete?.(row.original.id)}
              color="error"
            >
              <DeleteIcon />
            </IconButton>
          </Box>
        ),
      },
    ],
    [onEdit, onDelete]
  );

  const table = useReactTable({
    data,
    columns,
    state: {
      columnFilters,
      globalFilter,
      sorting,
    },
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          placeholder="Search all columns..."
          value={globalFilter ?? ''}
          onChange={(e) => setGlobalFilter(e.target.value)}
          size="small"
          sx={{ minWidth: 300 }}
        />
        <Button
          variant="outlined"
          onClick={() => {
            setGlobalFilter('');
            setColumnFilters([]);
            setSorting([]);
          }}
        >
          Clear Filters
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableCell
                    key={header.id}
                    sx={{ fontWeight: 'bold', cursor: header.column.getCanSort() ? 'pointer' : 'default' }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {{
                        asc: ' 🔼',
                        desc: ' 🔽',
                      }[header.column.getIsSorted() as string] ?? null}
                    </Box>
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableHead>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} hover>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={table.getFilteredRowModel().rows.length}
        page={table.getState().pagination.pageIndex}
        onPageChange={(_, page) => table.setPageIndex(page)}
        rowsPerPage={table.getState().pagination.pageSize}
        onRowsPerPageChange={(e) => table.setPageSize(Number(e.target.value))}
        rowsPerPageOptions={[5, 10, 25, 50]}
      />
    </Box>
  );
};

export default StudentsTable;