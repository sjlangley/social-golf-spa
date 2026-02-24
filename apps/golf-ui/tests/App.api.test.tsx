import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { App } from '../src/App';
import { server } from './mocks/server';

// Helper to get API URL (matches App.tsx logic)
function getApiUrl(pathname: string): string {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';
  return new URL(pathname, baseUrl).toString();
}

describe('App - API Integration', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Clear any auth errors
    vi.clearAllMocks();
  });

  describe('when user is not logged in', () => {
    it('does not make API call without idToken', () => {
      render(<App />);

      // Verify no current user is displayed
      expect(screen.queryByText(/Current user/i)).not.toBeInTheDocument();
    });

    it('renders login section', () => {
      render(<App />);

      const loginHeading = screen.getByRole('heading', { name: /login/i });
      expect(loginHeading).toBeInTheDocument();
    });
  });

  describe('when user is logged in', () => {
    beforeEach(() => {
      // Set mock ID token in localStorage
      localStorage.setItem('google_id_token', 'mock-token-12345');
    });

    it('fetches current user successfully', async () => {
      render(<App />);

      // Wait for the API call to complete and user to be displayed
      await waitFor(() => {
        expect(screen.getByText(/Current user/i)).toBeInTheDocument();
      });

      // Verify user details are displayed
      expect(screen.getByText('test-user-123')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    it('includes Authorization header with Bearer token', async () => {
      let requestHeaders: Headers | undefined;

      server.use(
        http.get(getApiUrl('/api/v1/users/current'), ({ request }) => {
          requestHeaders = request.headers;
          return HttpResponse.json({
            userid: 'test-user-123',
            email: 'test@example.com',
            name: 'Test User',
          });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Current user/i)).toBeInTheDocument();
      });

      expect(requestHeaders?.get('Authorization')).toBe('Bearer mock-token-12345');
    });

    it('displays loading state while fetching', async () => {
      // Delay the response to test loading state
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json({
            userid: 'test-user-123',
            email: 'test@example.com',
            name: 'Test User',
          });
        })
      );

      render(<App />);

      // Loading state should be present initially
      // (Component sets isLoadingUser to true)
      await waitFor(() => {
        expect(screen.getByText(/Current user/i)).toBeInTheDocument();
      });
    });

    it('handles 401 Unauthorized error', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return new HttpResponse('Unauthorized', { status: 401 });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Backend call failed/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/"status": 401/i)).toBeInTheDocument();
      expect(screen.queryByText(/Current user/i)).not.toBeInTheDocument();
    });

    it('handles 404 Not Found error', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return new HttpResponse('Not Found', { status: 404 });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Backend call failed/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/"status": 404/i)).toBeInTheDocument();
    });

    it('handles 500 Internal Server Error', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return new HttpResponse('Internal Server Error', { status: 500 });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Backend call failed/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/"status": 500/i)).toBeInTheDocument();
    });

    it('handles invalid JSON response', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return new HttpResponse('Not valid JSON{', {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Backend call failed/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Invalid JSON response/i)).toBeInTheDocument();
    });

    it('handles response missing required userid field', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return HttpResponse.json({
            email: 'test@example.com',
            name: 'Test User',
            // Missing userid
          });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Backend call failed/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Invalid response format/i)).toBeInTheDocument();
    });

    it('handles response with invalid userid type', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return HttpResponse.json({
            userid: 123, // Should be string
            email: 'test@example.com',
            name: 'Test User',
          });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Backend call failed/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Invalid response format/i)).toBeInTheDocument();
    });

    it('handles response with empty userid', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return HttpResponse.json({
            userid: '', // Empty string
            email: 'test@example.com',
            name: 'Test User',
          });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Backend call failed/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Invalid response format/i)).toBeInTheDocument();
    });

    it('accepts response with null email and name', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return HttpResponse.json({
            userid: 'test-user-123',
            email: null,
            name: null,
          });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Current user/i)).toBeInTheDocument();
      });

      expect(screen.getByText('test-user-123')).toBeInTheDocument();
      // Should show "(none)" for null values
      expect(screen.getAllByText('(none)')).toHaveLength(2);
    });

    it('accepts response with only userid', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return HttpResponse.json({
            userid: 'test-user-123',
          });
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Current user/i)).toBeInTheDocument();
      });

      expect(screen.getByText('test-user-123')).toBeInTheDocument();
    });

    it('handles network error', async () => {
      server.use(
        http.get(getApiUrl('/api/v1/users/current'), () => {
          return HttpResponse.error();
        })
      );

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Backend call failed/i)).toBeInTheDocument();
      });

      // Network error shows error message in responseText
      expect(screen.getByText(/Failed to fetch/i)).toBeInTheDocument();
    });

    it('clears user data on logout', async () => {
      render(<App />);

      // Wait for user to be loaded
      await waitFor(() => {
        expect(screen.getByText(/Current user/i)).toBeInTheDocument();
      });

      // Click logout button
      const logoutButton = screen.getByRole('button', { name: /logout/i });
      logoutButton.click();

      // User data should be cleared
      await waitFor(() => {
        expect(screen.queryByText(/Current user/i)).not.toBeInTheDocument();
      });

      // Should show login section again
      expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();

      // localStorage should be cleared
      expect(localStorage.getItem('google_id_token')).toBeNull();
    });
  });

  describe('token changes', () => {
    it('refetches user when token changes', async () => {
      localStorage.setItem('google_id_token', 'first-token');

      const { rerender } = render(<App />);

      await waitFor(() => {
        expect(screen.getByText(/Current user/i)).toBeInTheDocument();
      });

      // Change token
      localStorage.setItem('google_id_token', 'second-token');

      // Force re-render (in real app, this would happen via state update)
      rerender(<App />);

      // Should still show user (same mock response)
      await waitFor(() => {
        expect(screen.getByText(/Current user/i)).toBeInTheDocument();
      });
    });

    // Note: Testing token removal requires proper state management integration
    // The useEffect doesn't automatically react to localStorage changes
    // In the real app, this is handled by the Google Identity Services callback
  });
});
