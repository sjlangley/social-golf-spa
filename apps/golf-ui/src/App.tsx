import React from 'react';
import './App.css';

type BackendUser = {
  userid: string;
  email?: string | null;
  name?: string | null;
};

type BackendCallError = {
  url: string;
  status: number;
  statusText: string;
  responseText: string;
};

type GoogleCredentialResponse = {
  credential?: string;
};

type GoogleIdentityServices = {
  accounts: {
    id: {
      initialize: (config: {
        client_id: string;
        callback: (response: GoogleCredentialResponse) => void;
      }) => void;
      renderButton: (
        parent: HTMLElement,
        options: {
          theme?: 'outline' | 'filled_blue' | 'filled_black';
          size?: 'large' | 'medium' | 'small';
          text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin';
          width?: number;
          logo_alignment?: 'left' | 'center';
        }
      ) => void;
      prompt: () => void;
    };
  };
};

declare global {
  interface Window {
    google?: GoogleIdentityServices;
  }
}

const GIS_SCRIPT_SRC = 'https://accounts.google.com/gsi/client';

function loadGoogleIdentityServices(): Promise<void> {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }

  const existing = document.querySelector<HTMLScriptElement>(
    `script[src="${GIS_SCRIPT_SRC}"]`
  );

  if (existing) {
    return new Promise((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        reject(new Error('Timed out waiting for Google Identity Services to load'));
      }, 10_000);

      const check = () => {
        if (window.google?.accounts?.id) {
          window.clearTimeout(timeout);
          resolve();
          return;
        }
        window.setTimeout(check, 50);
      };

      check();
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = GIS_SCRIPT_SRC;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      if (!window.google?.accounts?.id) {
        reject(new Error('Google Identity Services script loaded but API not found'));
        return;
      }
      resolve();
    };

    script.onerror = () => {
      reject(new Error('Failed to load Google Identity Services script'));
    };

    document.head.appendChild(script);
  });
}

function getApiUrl(pathname: string): string {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';
  return new URL(pathname, baseUrl).toString();
}

function maskToken(token: string): string {
  if (token.length <= 16) {
    return '***';
  }
  return `${token.slice(0, 8)}…${token.slice(-8)}`;
}

export function App(): React.ReactElement {
  const googleClientId =
    (import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined) ?? '';

  const [idToken, setIdToken] = React.useState<string | null>(() => {
    return localStorage.getItem('google_id_token');
  });

  const [currentUser, setCurrentUser] = React.useState<BackendUser | null>(null);
  const [isLoadingUser, setIsLoadingUser] = React.useState(false);
  const [backendError, setBackendError] = React.useState<BackendCallError | null>(null);
  const [authError, setAuthError] = React.useState<string | null>(null);
  const loginButtonRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!idToken) {
      setCurrentUser(null);
      setBackendError(null);
      return;
    }

    const token = idToken;

    const url = getApiUrl('/api/test');
    const controller = new AbortController();

    async function fetchCurrentUser() {
      setIsLoadingUser(true);
      setBackendError(null);

      try {
        console.log('[auth] Fetching current user from backend', {
          url,
          hasToken: true,
          tokenPreview: maskToken(token),
        });

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        });

        const responseText = await response.text();
        if (!response.ok) {
          console.error('[auth] Backend /api/test failed', {
            url,
            status: response.status,
            statusText: response.statusText,
            responseText,
          });
          setCurrentUser(null);
          setBackendError({
            url,
            status: response.status,
            statusText: response.statusText,
            responseText,
          });
          return;
        }

        const parsed = JSON.parse(responseText) as BackendUser;
        console.log('[auth] Backend /api/test succeeded', {
          url,
          userid: parsed.userid,
          email: parsed.email ?? null,
          name: parsed.name ?? null,
        });
        setCurrentUser(parsed);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error('[auth] Backend /api/test threw', { url, message });
        setCurrentUser(null);
        setBackendError({
          url,
          status: 0,
          statusText: 'Network error',
          responseText: message,
        });
      } finally {
        setIsLoadingUser(false);
      }
    }

    void fetchCurrentUser();
    return () => controller.abort();
  }, [idToken]);

  function handleLogout() {
    localStorage.removeItem('google_id_token');
    setIdToken(null);
    setCurrentUser(null);
    setBackendError(null);
    setAuthError(null);
    console.log('[auth] Logged out');
  }

  // Initialize Google Sign-In button on mount if not logged in
  React.useEffect(() => {
    if (idToken || !googleClientId || googleClientId.startsWith('your-')) {
      return;
    }

    async function initGoogleButton() {
      try {
        await loadGoogleIdentityServices();
        const google = window.google;
        if (!google?.accounts?.id || !loginButtonRef.current) {
          return;
        }

        google.accounts.id.initialize({
          client_id: googleClientId,
          callback: (response) => {
            const credential = response.credential;
            if (!credential) {
              console.error('[auth] GIS callback missing credential', { response });
              setAuthError('Google login did not return a credential.');
              return;
            }

            console.log('[auth] Received Google ID token', { tokenPreview: maskToken(credential) });

            localStorage.setItem('google_id_token', credential);
            setIdToken(credential);
          },
        });

        google.accounts.id.renderButton(loginButtonRef.current, {
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          width: 250,
        });

        console.log('[auth] Google sign-in button rendered on mount');
      } catch (error) {
        console.error('[auth] Failed to initialize Google button on mount', error);
      }
    }

    void initGoogleButton();
  }, [idToken, googleClientId]);

  return (
    <div className="min-h-screen flex flex-col font-sans bg-gray-100">
      <header className="bg-slate-800 text-white p-8 text-center shadow-md">
        <h1 className="m-0 text-3xl font-bold">Caringbah Social Golf Club</h1>
        <p className="mt-2 text-lg opacity-90">Golf Club Management System</p>
      </header>
      <main className="flex-1 p-8">
        <div className="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow">
          {!idToken && (
            <>
              <h2 className="text-2xl font-semibold mb-2">Welcome</h2>
              <p className="mb-2">This is a minimal React 19 + TypeScript + Vite application.</p>
              <p className="mb-4">
                The application is part of a monorepo and provides the frontend for the Caringbah Social
                Golf Club management system.
              </p>
              <div className="mb-6">
                <h3 className="text-xl font-semibold mb-2">Features:</h3>
                <ul className="list-disc list-inside space-y-1">
                  <li>React 19 with TypeScript</li>
                  <li>Vite for fast development</li>
                  <li>Vitest for unit testing</li>
                  <li>ESLint + Prettier code quality</li>
                  <li>Tailwind CSS for rapid UI styling</li>
                </ul>
              </div>

              <div className="border-t pt-6">
                <h3 className="text-xl font-semibold mb-3">Login</h3>
                <div ref={loginButtonRef} className="inline-block"></div>

                {authError && (
                  <p className="mt-3 text-sm text-red-700" role="alert">
                    {authError}
                  </p>
                )}
              </div>
            </>
          )}

          {idToken && (
            <>
              <div className="flex items-center justify-between gap-4">
                <h2 className="text-2xl font-semibold">Authenticated</h2>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-3 py-2 rounded border border-slate-300"
                >
                  Logout
                </button>
              </div>

              <p className="mt-2 text-sm text-slate-600">Calling backend: GET /api/test</p>

              {isLoadingUser && <p className="mt-4" role="status">Loading user…</p>}

              {currentUser && (
                <div className="mt-4">
                  <h3 className="text-xl font-semibold mb-2">Current user</h3>
                  <dl className="grid grid-cols-1 gap-2">
                    <div>
                      <dt className="text-sm text-slate-600">User ID</dt>
                      <dd className="font-mono text-sm">{currentUser.userid}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-slate-600">Email</dt>
                      <dd className="text-sm">{currentUser.email ?? '(none)'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-slate-600">Name</dt>
                      <dd className="text-sm">{currentUser.name ?? '(none)'}</dd>
                    </div>
                  </dl>
                </div>
              )}

              {backendError && (
                <div className="mt-4" role="alert">
                  <h3 className="text-xl font-semibold text-red-800">Backend call failed</h3>
                  <pre className="mt-2 whitespace-pre-wrap text-sm bg-gray-100 p-4 rounded">
{JSON.stringify(backendError, null, 2)}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
