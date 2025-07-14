import { useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';
import { useAuth } from './useAuth';

export interface Course {
  id: string;
  name: string;
  code: string;
  description?: string;
  semester: string;
  year: number;
  instructor?: string;
  enrolled?: number;
  capacity?: number;
}

interface UseCoursesResult {
  courses: Course[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export const useCourses = (): UseCoursesResult => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { state: authState } = useAuth();

  const fetchCourses = async () => {
    if (!authState.isAuthenticated) {
      setCourses([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.get<Course[]>('/courses');
      setCourses(data);
    } catch (err) {
      console.error('Failed to fetch courses:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch courses');
      setCourses([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, [authState.isAuthenticated]);

  return {
    courses,
    loading,
    error,
    refetch: fetchCourses,
  };
};