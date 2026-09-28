import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthContext'
import { GuestRoute, ProtectedRoute } from './auth/ProtectedRoute'
import { AppLayout } from './layouts/AppLayout'
import { PublicLayout } from './layouts/PublicLayout'
import { AboutPage } from './pages/AboutPage'
import { AdminLayout } from './layouts/AdminLayout'
import { AdminConfigPage } from './pages/admin/AdminConfigPage'
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage'
import { AdminFacultyPriorsPage } from './pages/admin/AdminFacultyPriorsPage'
import { AdminFeedbackPage } from './pages/admin/AdminFeedbackPage'
import { AdminOnetPage } from './pages/admin/AdminOnetPage'
import { AdminQuestionnairePage } from './pages/admin/AdminQuestionnairePage'
import { AdminRunDetailPage } from './pages/admin/AdminRunDetailPage'
import { AdminRunsPage } from './pages/admin/AdminRunsPage'
import { AdminStudentDetailPage } from './pages/admin/AdminStudentDetailPage'
import { AdminStudentsPage } from './pages/admin/AdminStudentsPage'
import { AssessmentCompletePage } from './pages/AssessmentCompletePage'
import { AssessmentPage } from './pages/AssessmentPage'
import { DashboardPage } from './pages/DashboardPage'
import { RecommendationDetailPage } from './pages/RecommendationDetailPage'
import { RecommendationsPage } from './pages/RecommendationsPage'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ProfilePage } from './pages/ProfilePage'
import { RegisterPage } from './pages/RegisterPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route
          path="/login"
          element={
            <GuestRoute>
              <LoginPage />
            </GuestRoute>
          }
        />
        <Route
          path="/register"
          element={
            <GuestRoute>
              <RegisterPage />
            </GuestRoute>
          }
        />
      </Route>
      <Route
        element={
          <ProtectedRoute roles={['student']}>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/assessment" element={<AssessmentPage />} />
        <Route path="/assessment/complete" element={<AssessmentCompletePage />} />
        <Route path="/recommendations/:runId" element={<RecommendationsPage />} />
        <Route path="/recommendations/:runId/items/:itemId" element={<RecommendationDetailPage />} />
      </Route>
      <Route
        element={
          <ProtectedRoute roles={['admin']}>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route element={<AdminLayout />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/admin/students" element={<AdminStudentsPage />} />
          <Route path="/admin/students/:studentId" element={<AdminStudentDetailPage />} />
          <Route path="/admin/recommendations" element={<AdminRunsPage />} />
          <Route path="/admin/recommendations/:runId" element={<AdminRunDetailPage />} />
          <Route path="/admin/feedback" element={<AdminFeedbackPage />} />
          <Route path="/admin/onet" element={<AdminOnetPage />} />
          <Route path="/admin/questionnaire" element={<AdminQuestionnairePage />} />
          <Route path="/admin/configuration" element={<AdminConfigPage />} />
          <Route path="/admin/faculty-priors" element={<AdminFacultyPriorsPage />} />
        </Route>
      </Route>
      <Route element={<PublicLayout />}>
        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
