import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
  Box,
  Typography,
} from '@mui/material';
import { Student } from '../types';

const studentSchema = z.object({
  givenName: z.string().min(1, 'First name is required').max(50, 'First name must be less than 50 characters'),
  familyName: z.string().min(1, 'Last name is required').max(50, 'Last name must be less than 50 characters'),
  email: z.string().email('Invalid email address'),
  studentId: z.string().min(1, 'Student ID is required').max(20, 'Student ID must be less than 20 characters'),
  enrollmentDate: z.string().min(1, 'Enrollment date is required'),
  status: z.enum(['active', 'inactive', 'suspended']),
  grade: z.number().min(0, 'Grade must be at least 0').max(100, 'Grade must be at most 100').optional(),
});

type StudentFormData = z.infer<typeof studentSchema>;

interface StudentFormProps {
  student?: Student | null;
  onSave: (data: Omit<Student, 'id'>) => void;
  onCancel: () => void;
}

const StudentForm: React.FC<StudentFormProps> = ({ student, onSave, onCancel }) => {
  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
    reset,
  } = useForm<StudentFormData>({
    resolver: zodResolver(studentSchema),
    defaultValues: {
      givenName: student?.givenName || '',
      familyName: student?.familyName || '',
      email: student?.email || '',
      studentId: student?.studentId || '',
      enrollmentDate: student?.enrollmentDate || new Date().toISOString().split('T')[0],
      status: student?.status || 'active',
      grade: student?.grade || undefined,
    },
    mode: 'onChange',
  });

  const onSubmit = (data: StudentFormData) => {
    onSave(data as Omit<Student, 'id'>);
    reset();
  };

  const handleCancel = () => {
    reset();
    onCancel();
  };

  return (
    <>
      <DialogTitle>
        {student ? 'Edit Student' : 'Add New Student'}
      </DialogTitle>
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 400 }}>
            <Controller
              name="givenName"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="First Name"
                  error={!!errors.givenName}
                  helperText={errors.givenName?.message}
                  fullWidth
                />
              )}
            />

            <Controller
              name="familyName"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Last Name"
                  error={!!errors.familyName}
                  helperText={errors.familyName?.message}
                  fullWidth
                />
              )}
            />

            <Controller
              name="email"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Email"
                  type="email"
                  error={!!errors.email}
                  helperText={errors.email?.message}
                  fullWidth
                />
              )}
            />

            <Controller
              name="studentId"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Student ID"
                  error={!!errors.studentId}
                  helperText={errors.studentId?.message}
                  fullWidth
                />
              )}
            />

            <Controller
              name="enrollmentDate"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Enrollment Date"
                  type="date"
                  error={!!errors.enrollmentDate}
                  helperText={errors.enrollmentDate?.message}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              )}
            />

            <Controller
              name="status"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Status"
                  select
                  error={!!errors.status}
                  helperText={errors.status?.message}
                  fullWidth
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                  <MenuItem value="suspended">Suspended</MenuItem>
                </TextField>
              )}
            />

            <Controller
              name="grade"
              control={control}
              render={({ field: { value, onChange, ...field } }) => (
                <TextField
                  {...field}
                  label="Grade (%)"
                  type="number"
                  value={value || ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    onChange(val === '' ? undefined : Number(val));
                  }}
                  error={!!errors.grade}
                  helperText={errors.grade?.message}
                  fullWidth
                  inputProps={{ min: 0, max: 100 }}
                />
              )}
            />
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleCancel} color="inherit">
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={!isValid}
          >
            {student ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </>
  );
};

export default StudentForm;