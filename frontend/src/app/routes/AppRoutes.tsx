import React from 'react';
import { Route, Routes } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';
import CoursesPage from '../../pages/CoursesPage';
import SSODebug from '../../pages/SSODebug';
import Tasks from '../../pages/Tasks';
import TaskDetail from '../../pages/TaskDetail';
import UsersPage from '../../pages/UsersPage';
import UserDetailPage from '../../pages/UserDetailPage';
import UserEditPage from '../../pages/UserEditPage';
import OrganizationsPage from '../../pages/OrganizationsPage';
import OrganizationDetailPage from '../../pages/OrganizationDetailPage';
import OrganizationEditPage from '../../pages/OrganizationEditPage';
import OrganizationCreatePage from '../../pages/OrganizationCreatePage';
import CourseFamiliesPage from '../../pages/CourseFamiliesPage';
import CourseFamilyDetailPage from '../../pages/CourseFamilyDetailPage';
import CourseFamilyEditPage from '../../pages/CourseFamilyEditPage';
import CourseFamilyCreatePage from '../../pages/CourseFamilyCreatePage';
import CourseCreatePage from '../../pages/CourseCreatePage';
import CourseDetailPage from '../../pages/CourseDetailPage';
import RolesPage from '../../pages/RolesPage';
import ExamplesPage from '../../pages/ExamplesPage';
import ExampleDetailPage from '../../pages/ExampleDetailPage';

const AppRoutes: React.FC = () => (
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/courses" element={<CoursesPage />} />
    <Route path="/admin/courses" element={<CoursesPage />} />
    <Route path="/admin/courses/create" element={<CourseCreatePage />} />
    <Route path="/admin/courses/:id" element={<CourseDetailPage />} />
    <Route path="/admin/tasks" element={<Tasks />} />
    <Route path="/admin/tasks/:taskId" element={<TaskDetail />} />
    <Route path="/admin/users" element={<UsersPage />} />
    <Route path="/admin/users/:id" element={<UserDetailPage />} />
    <Route path="/admin/users/:id/edit" element={<UserEditPage />} />
    <Route path="/admin/organizations" element={<OrganizationsPage />} />
    <Route path="/admin/organizations/create" element={<OrganizationCreatePage />} />
    <Route path="/admin/organizations/:id" element={<OrganizationDetailPage />} />
    <Route path="/admin/organizations/:id/edit" element={<OrganizationEditPage />} />
    <Route path="/admin/course-families" element={<CourseFamiliesPage />} />
    <Route path="/admin/course-families/create" element={<CourseFamilyCreatePage />} />
    <Route path="/admin/course-families/:id" element={<CourseFamilyDetailPage />} />
    <Route path="/admin/course-families/:id/edit" element={<CourseFamilyEditPage />} />
    <Route path="/admin/roles" element={<RolesPage />} />
    <Route path="/admin/examples" element={<ExamplesPage />} />
    <Route path="/admin/examples/:id" element={<ExampleDetailPage />} />
    <Route path="/course/:courseId" element={<Dashboard />} />
    <Route path="/admin/*" element={<Dashboard />} />
    <Route path="/debug/sso" element={<SSODebug />} />
  </Routes>
);

export default AppRoutes;
