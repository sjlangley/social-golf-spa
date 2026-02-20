# Golf UI

React 19 + TypeScript + Vite frontend for the Caringbah Social Golf Club management system.

## Quick Start

### Prerequisites
- Node.js 20+
- npm 10+

### Installation

```bash
cd apps/golf-ui
npm install
```

### Development

```bash
npm run dev
```

Starts development server at http://localhost:5173

### Building

```bash
npm run build
```

Builds optimized production bundle to `dist/`

### Testing

```bash
# Run tests once
npm test

# Run tests in watch mode
npm run test:watch

# Run tests once with coverage
npm run test:ci

# Open Vitest UI
npm run test:ui
```

### Code Quality

```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check
```

## Project Structure

```
src/
  main.tsx          # React app entry point
  App.tsx           # Root component
  App.css           # Root styles

tests/
  App.test.tsx      # Component tests

public/
  vite.svg          # Vite logo

index.html          # HTML entry point
package.json        # Dependencies and scripts
tsconfig.json       # TypeScript configuration
vite.config.ts      # Vite configuration
vitest.config.ts    # Vitest configuration
```

## Configuration Files

- **package.json** – Dependencies and npm scripts
- **tsconfig.json** – TypeScript compiler options (strict mode enabled)
- **.env.example** – Environment variables template
- **.gitignore** – Git ignore patterns
- **eslint.config.js** – ESLint rules (Google TS style)
- **.prettierrc** – Prettier formatting config
- **vite.config.ts** – Vite build tool config
- **vitest.config.ts** – Vitest testing framework config

## Environment Variables

Create `.env.local` based on `.env.example`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

## Technology Stack

- **React 19** – UI library
- **TypeScript 5** – Type safety
- **Vite 5** – Build tool
- **Vitest** – Unit testing framework
- **@testing-library/react** – Component testing utilities
- **ESLint** – Code linting
- **Prettier** – Code formatting

## Troubleshooting

### Port 5173 already in use
```bash
npm run dev -- --port 3000
```

### Module not found errors
```bash
rm -rf node_modules package-lock.json
npm install
```

### Tests not running
```bash
npm run test -- --no-coverage
```

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes
3. Run tests: `npm run test:ci`
4. Run linting: `npm run lint`
5. Format code: `npm run format`
6. Commit: `git commit -m "feat: description"`
7. Push: `git push origin feature/name`

## License

MIT
