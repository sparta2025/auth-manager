import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./store/auth";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";

import { LoginPage }          from "./pages/auth/LoginPage";
import { RegisterPage }       from "./pages/auth/RegisterPage";
import { ForgotPasswordPage } from "./pages/auth/ForgotPasswordPage";
import { ResetPasswordPage }  from "./pages/auth/ResetPasswordPage";
import { DashboardPage }      from "./pages/auth/DashboardPage";
import { ProfilePage }        from "./pages/auth/ProfilePage";
import { SessionsPage }       from "./pages/auth/SessionsPage";
import { TwoFactorPage }      from "./pages/auth/TwoFactorPage";

import { UsersPage }         from "./pages/admin/UsersPage";
import { RolesPage }         from "./pages/admin/RolesPage";
import { PermissionsPage }   from "./pages/admin/PermissionsPage";
import { NotificationsPage } from "./pages/admin/NotificationsPage";
import { PolicyPage } from "./pages/admin/PolicyPage";
import { AuditLogPage }      from "./pages/admin/AuditLogPage";

import { ReportsPage }   from "./pages/resources/ReportsPage";
import { DocumentsPage } from "./pages/resources/DocumentsPage";
import { SettingsPage }  from "./pages/resources/SettingsPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: { fontSize: "14px", borderRadius: "10px" },
          }}
        />
        <Routes>
          {/* Public */}
          <Route path="/login"           element={<LoginPage />} />
          <Route path="/register"        element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password"  element={<ResetPasswordPage />} />

          {/* Protected */}
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard"           element={<DashboardPage />} />
            <Route path="/profile"             element={<ProfilePage />} />
            <Route path="/sessions"            element={<SessionsPage />} />
            <Route path="/2fa"                 element={<TwoFactorPage />} />

            <Route path="/admin/users"         element={<UsersPage />} />
            <Route path="/admin/roles"         element={<RolesPage />} />
            <Route path="/admin/permissions"   element={<PermissionsPage />} />
            <Route path="/admin/notifications" element={<NotificationsPage />} />
            <Route path="/admin/audit-log"     element={<AuditLogPage />} />
            <Route path="/admin/policy"        element={<PolicyPage />} />

            <Route path="/reports"             element={<ReportsPage />} />
            <Route path="/documents"           element={<DocumentsPage />} />
            <Route path="/settings"            element={<SettingsPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
