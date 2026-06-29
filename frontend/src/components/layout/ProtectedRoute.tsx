import { Navigate } from "react-router-dom";
import { useAuth } from "../../store/auth";
import { PageLoader } from "../ui";
export function ProtectedRoute({ children }:{children:React.ReactNode}) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <PageLoader/>;
  if (!isAuthenticated) return <Navigate to="/login" replace/>;
  return <>{children}</>;
}
