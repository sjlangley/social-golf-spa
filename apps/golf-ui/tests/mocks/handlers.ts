import { http, HttpResponse } from 'msw';

// Default base URL for API (can be overridden by VITE_API_BASE_URL env var)
const getApiUrl = (path: string) => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  return new URL(path, baseUrl).toString();
};

export const handlers = [
  // Mock the current user endpoint
  http.get(getApiUrl('/api/v1/users/current'), () => {
    return HttpResponse.json({
      userid: 'test-user-123',
      email: 'test@example.com',
      name: 'Test User',
    });
  }),
];
