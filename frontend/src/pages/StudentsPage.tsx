import React, { useState } from 'react';
import { Typography, Box, Button, Dialog } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import StudentsTable from '../components/StudentsTable';
import StudentForm from '../components/StudentForm';
import { mockStudents } from '../utils/mockData';
import { Student } from '../types';

const StudentsPage: React.FC = () => {
  const [students, setStudents] = useState<Student[]>(mockStudents);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);

  const handleAddStudent = () => {
    setEditingStudent(null);
    setIsFormOpen(true);
  };

  const handleEditStudent = (student: Student) => {
    setEditingStudent(student);
    setIsFormOpen(true);
  };

  const handleDeleteStudent = (studentId: string) => {
    if (window.confirm('Are you sure you want to delete this student?')) {
      setStudents(students.filter(s => s.id !== studentId));
    }
  };

  const handleSaveStudent = (studentData: Omit<Student, 'id'>) => {
    if (editingStudent) {
      setStudents(students.map(s => 
        s.id === editingStudent.id 
          ? { ...studentData, id: editingStudent.id }
          : s
      ));
    } else {
      const newStudent: Student = {
        ...studentData,
        id: Date.now().toString(),
      };
      setStudents([...students, newStudent]);
    }
    setIsFormOpen(false);
    setEditingStudent(null);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingStudent(null);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Students
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddStudent}
        >
          Add Student
        </Button>
      </Box>

      <StudentsTable
        data={students}
        onEdit={handleEditStudent}
        onDelete={handleDeleteStudent}
      />

      <Dialog
        open={isFormOpen}
        onClose={handleCloseForm}
        maxWidth="sm"
        fullWidth
      >
        <StudentForm
          student={editingStudent}
          onSave={handleSaveStudent}
          onCancel={handleCloseForm}
        />
      </Dialog>
    </Box>
  );
};

export default StudentsPage;