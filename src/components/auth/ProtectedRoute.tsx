import { ReactNode, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useApp } from '@/context/AppContext';
import { Card, CardContent } from '@/components/ui/card';
import { Logo } from '@/components/Logo';

interface ProtectedRouteProps {
  children: ReactNode;
}

/**
 * ProtectedRoute Component
 * Wrapper for routes that require authentication
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { auth } = useApp();
  const location = useLocation();

  useEffect(() => {
    // Store the intended destination for redirect after login
    if (!auth.isAuthenticated && !auth.isLoading) {
      sessionStorage.setItem('auth_redirect', location.pathname);
    }
  }, [auth.isAuthenticated, auth.isLoading, location.pathname]);

  // Show loading state while checking authentication
  if (auth.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center space-y-4">
              <div className="flex justify-center mb-4">
                <Logo size="sm" />
              </div>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
              <p className="text-sm text-gray-600">Loading...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Render protected content
  return <>{children}</>;
}