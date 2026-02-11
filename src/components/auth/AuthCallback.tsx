import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '@/context/AppContext';
import { authApi } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Logo } from '@/components/Logo';

/**
 * AuthCallback Component
 * Handles OAuth callback from Google and stores tokens
 */
export default function AuthCallback() {
  const { checkAuth } = useApp();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get tokens from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const accessToken = urlParams.get('access_token');
        const refreshToken = urlParams.get('refresh_token');
        
        if (!accessToken || !refreshToken) {
          throw new Error('No tokens received from authentication');
        }
        
        // Store tokens in localStorage
        localStorage.setItem('auth_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        
        // Verify authentication and load user data
        await checkAuth();
        
        // Get the intended destination from session storage or default to dashboard
        const intendedDestination = sessionStorage.getItem('auth_redirect') || '/';
        sessionStorage.removeItem('auth_redirect');
        
        // Redirect to the intended destination
        navigate(intendedDestination, { replace: true });
      } catch (err) {
        console.error('Authentication callback failed:', err);
        setError(err instanceof Error ? err.message : 'Authentication failed');
        
        // Redirect to login after a delay
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      }
    };

    handleCallback();
  }, [checkAuth, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center space-y-4">
              <div className="flex justify-center mb-4">
                <Logo size="sm" />
              </div>
              <div className="text-center space-y-2">
                <div className="w-12 h-12 mx-auto rounded-full bg-red-100 flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-red-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-900">Authentication Failed</h2>
                <p className="text-sm text-gray-600">{error}</p>
                <p className="text-xs text-gray-500 mt-4">Redirecting to login...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center space-y-4">
            <div className="flex justify-center mb-4">
              <Logo size="sm" />
            </div>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            <div className="text-center space-y-2">
              <h2 className="text-xl font-semibold text-gray-900">Completing Sign In</h2>
              <p className="text-sm text-gray-600">Please wait while we set up your account...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}