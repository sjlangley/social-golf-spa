import './App.css';

export function App(): React.ReactElement {
  return (
    <div className="min-h-screen flex flex-col font-sans bg-gray-100">
      <header className="bg-slate-800 text-white p-8 text-center shadow-md">
        <h1 className="m-0 text-3xl font-bold">Caringbah Social Golf Club</h1>
        <p className="mt-2 text-lg opacity-90">Golf Club Management System</p>
      </header>
      <main className="flex-1 p-8">
        <div className="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-2">Welcome</h2>
          <p className="mb-2">This is a minimal React 19 + TypeScript + Vite application.</p>
          <p className="mb-4">
            The application is part of a monorepo and provides the frontend for the Caringbah Social
            Golf Club management system.
          </p>
          <div>
            <h3 className="text-xl font-semibold mb-2">Features:</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>React 19 with TypeScript</li>
              <li>Vite for fast development</li>
              <li>Vitest for unit testing</li>
              <li>ESLint + Prettier code quality</li>
              <li>Tailwind CSS for rapid UI styling</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
