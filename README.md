# Caringbah Social Golf Club

A modern golf club management system for tracking members, scores, matches, handicaps, and prizes. Built for the Caringbah Social Golf Club in Australia.

**Optimized for Google Cloud Platform free tier** – Runs serverless with near-zero operational overhead.

[![CI](https://github.com/sjlangley/csocgolf-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/sjlangley/csocgolf-v2/actions/workflows/ci.yml)

---

## ⚠️ CRITICAL FOR CONTRIBUTORS ⚠️

**BEFORE COMMITTING ANY CODE CHANGES:**
1. Navigate to the correct service directory (cd apps/golf-api, cd apps/golf-ui, or cd apps/handicap-calculator)
2. Run ALL format, lint, type checking, and test commands (see [Before Committing](#before-committing) section)
3. Fix ALL errors until all checks pass
4. Only then commit your changes

**This is MANDATORY. CI will fail otherwise.**

---

## What This Application Does

This system helps our golf club:
- **Manage Members** – Track player profiles, contact info, and statistics
- **Record Scores** – Log golf scores across different courses and tees
- **Track Matches** – Record match results for up to 26 players with prize assignments
- **Calculate Handicaps** – Automatically compute handicaps following Australian Golf standards (via background Pub/Sub job)
- **Award Prizes** – Track nearest pin, longest drive, and drive & chip winners

## Architecture Overview (Free Tier Optimized)

```
┌───────────────────────────────────────┐
│   React SPA (Cloud Storage)           │
│   Served from static bucket           │
│   • Vite + TypeScript                 │
│   • TanStack Query                    │
│   • Google Sign-In                    │
└──────────────┬────────────────────────┘
               │
               │ HTTPS (ID Token)
               │
               ▼
┌───────────────────────────────────────┐
│   FastAPI Backend (Cloud Run)         │
│   • Token verification                │
│   • Score recording                   │
│   • Pub/Sub publisher                 │
│   • API responses in <500ms           │
└───┬───────────────────────────────────┘
    │
    ├──────────────────────┬──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
Firestore            Pub/Sub Topic         Firestore
  • users            \"score.created\"        (read)
  • members
  • scores                 ▼
  • matches         ┌─────────────────────┐
  • handicaps       │ Handicap Calculator │
  • clubs/courses   │ (Cloud Run Service) │
  • tees            │ • Calculates async  │
                    │ • Writes handicaps  │
                    └─────────────────────┘
```

All services covered by free tier quotas (< 100 members, < 50 API calls/day).

## Prerequisites

- **Node.js** 20+ (for frontend development)
- **Python** 3.12+ (for backend development)
- **Google Cloud Project** (free tier) with:
  - Firestore enabled (50K reads/20K writes/day)
  - Cloud Run API enabled
  - Service Account with Firestore access
- **Google OAuth 2.0 Client ID** for web application

## Local Development

### Backend Setup

```bash
cd apps/golf-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

Create `apps/golf-api/.env`:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
FIRESTORE_EMULATOR_HOST=localhost:8080  # Optional, for local Firestore emulator
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=DEBUG
PUBSUB_TOPIC_NAME=score.created  # Pub/Sub topic for score events
```

Run the backend:
```bash
# With Firestore emulator (recommended for local dev)
gcloud emulators firestore start --host-port=localhost:8080

# In another terminal
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Handicap Calculator Setup (Local Development)

The handicap calculator is a separate service that listens to the Pub/Sub topic for score events.

```bash
cd apps/handicap-calculator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

Create `apps/handicap-calculator/.env`:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
FIRESTORE_EMULATOR_HOST=localhost:8080  # Use same emulator as backend
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
PUBSUB_SUBSCRIPTION_NAME=score.created-calculator
LOG_LEVEL=DEBUG
PORT=8001
```

Run the handicap calculator:
```bash
uvicorn app.main:app --reload --port 8001
```

In local development, the Pub/Sub emulator needs to be running. For testing without Pub/Sub, manually trigger calculations via:
```bash
curl -X POST http://localhost:8001/calculate \
  -H "Content-Type: application/json" \
  -d '{"memberId":"member123"}'
```

### Frontend Setup

```bash
cd apps/golf-ui
npm install
```

Create `apps/golf-ui/.env.local`:
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

Run the frontend:
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Required Environment Variables

### Backend (Cloud Run)
- `GOOGLE_CLOUD_PROJECT` – GCP project ID
- `CORS_ORIGINS` – Comma-separated list of allowed origins
- `LOG_LEVEL` – Logging level (INFO, DEBUG, WARNING, ERROR)
- `PUBSUB_TOPIC_NAME` – Pub/Sub topic name for score events (default: `score.created`)
- `GOOGLE_APPLICATION_CREDENTIALS` – Path to service account JSON (auto-provided in Cloud Run)

### Handicap Calculator (Cloud Run Service)
- `GOOGLE_CLOUD_PROJECT` – GCP project ID
- `LOG_LEVEL` – Logging level (INFO, DEBUG, WARNING, ERROR)
- `PUBSUB_SUBSCRIPTION_NAME` – Pub/Sub subscription name (default: `score.created-calculator`)
- `GOOGLE_APPLICATION_CREDENTIALS` – Path to service account JSON (auto-provided in Cloud Run)

### Frontend (Build time)
- `VITE_API_BASE_URL` – Backend API base URL
- `VITE_GOOGLE_CLIENT_ID` – Google OAuth 2.0 client ID

## Testing

### Backend Tests (pytest)
```bash
cd apps/golf-api
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/unit              # Unit tests only
pytest --cov=app               # With coverage
```

### Handicap Calculator Tests (pytest)
```bash
cd apps/handicap-calculator
pytest                          # Run all tests
pytest --cov=app               # With coverage
```

### Frontend Tests (vitest)
```bash
cd apps/golf-ui
npm test                       # Run tests in watch mode
npm run test:ci                # Single run for CI
npm run test:coverage          # With coverage report
```

### Test Coverage Requirements

**Minimum coverage: 80%** across all services. Before committing code:

```bash
# Backend
cd apps/golf-api
pytest --cov=app --cov-fail-under=80

# Handicap Calculator
cd apps/handicap-calculator
pytest --cov=app --cov-fail-under=80

# Frontend
cd apps/golf-ui
npm run test:coverage -- --coverage-threshold=80
```

All CI builds enforce this minimum.

### Code Style & Linting

**All code must follow [Google Style Guide](https://google.github.io/styleguide/) conventions** for your language:
- **Python:** [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) (enforced via ruff + pyright)
- **TypeScript:** [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html) (enforced via eslint + prettier)

Before committing, run linting, type checking, and formatting:

```bash
# Backend (Python)
cd apps/golf-api
ruff check .                   # Lint with ruff (Google style)
ruff format .                  # Auto-format with ruff
pyright .                      # Type check with pyright

# Handicap Calculator (Python)
cd apps/handicap-calculator
ruff check .                   # Lint with ruff
ruff format .                  # Auto-format with ruff
pyright .                      # Type check with pyright

# Frontend (TypeScript)
cd apps/golf-ui
npm run lint                   # ESLint (Google-based rules)
npm run format                 # Prettier (TypeScript formatting)
```

Linting, type checking, and formatting issues will block CI/CD. See [.github/copilot-instructions.md](.github/copilot-instructions.md) for detailed style conventions.

## Deployment (Free Tier Optimized)

We deploy to Google Cloud Run using GitHub Actions. The deployment workflow:

1. **CI Checks** – Run tests, linting, and type checking
2. **Build Images** – Build Docker images for backend and handicap calculator
3. **Push** – Push images to Artifact Registry
4. **Deploy Backend** – Deploy main API to Cloud Run (min=0, max=10 instances)
5. **Deploy Calculator** – Deploy handicap calculator to Cloud Run (min=0, max=5 instances)
6. **Deploy Frontend** – Upload static assets to Cloud Storage bucket with custom domain

All services are within free tier limits (~2M requests/month combined).

### Frontend Custom Domain Setup

You can serve the React SPA directly from a custom domain (e.g., `csocgolf.com`) using Cloud Storage:

```bash
# 1. Create a Cloud Storage bucket with your domain name
gsutil mb gs://csocgolf.com

# 2. Enable static website hosting on the bucket
gsutil web set -m index.html gs://csocgolf.com

# 3. Point your domain's DNS to Cloud Storage
# Add a CNAME record in your DNS provider:
# Hostname: csocgolf.com (or www.csocgolf.com)
# Target: c.storage.googleapis.com

# 4. Verify domain ownership in Google Cloud Console
# Navigate to: Cloud Storage > Buckets > [bucket] > Configuration

# 5. Google automatically provisions a free SSL certificate
# (Setup takes ~15 minutes after verification)

# 6. Build and deploy the frontend
cd frontend
npm run build
gsutil -m cp -r dist/* gs://csocgolf.com/

# 7. Set bucket CORS policy for API calls
gsutil cors set - gs://csocgolf.com << 'EOF'
[
  {
    "origin": ["https://api.csocgolf.com"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF
```

**Benefits:**
- Free HTTPS with Google-managed SSL
- No additional costs beyond Cloud Storage (5GB free)
- Direct serving from Cloud Storage (no CDN charges)
- Automatic DNS failover and global distribution

See [docs/architecture.md](docs/architecture.md) for detailed deployment instructions and architecture decisions.

## Project Structure

```
├── apps/
│   ├── golf-ui/              # React SPA (Node.js)
│   │   ├── src/
│   │   ├── tests/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   ├── golf-api/             # FastAPI backend (main API)
│   │   ├── app/
│   │   │   ├── main.py      # FastAPI app entry point
│   │   │   ├── models.py    # Pydantic models
│   │   │   ├── routes/      # API route handlers
│   │   │   ├── services/    # Business logic (Firestore, etc.)
│   │   │   └── auth/        # Authentication & authorization
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── handicap-calculator/  # Pub/Sub subscriber service
│       ├── app/
│       │   ├── main.py      # Cloud Run HTTP endpoint
│       │   ├── models.py    # Pydantic models
│       │   └── services/    # Handicap calculation logic
│       ├── tests/
│       ├── pyproject.toml
│       └── Dockerfile
├── docs/
│   └── architecture.md      # Architecture documentation
└── .github/
    ├── workflows/           # CI/CD workflows
    └── copilot-instructions.md
```

## Contributing

### Before Committing

**⚠️ CRITICAL - ALL CODE CHANGES MUST MEET THESE REQUIREMENTS BEFORE COMMITTING ⚠️**

**This is NOT a suggestion. This is a MANDATORY requirement. Skipping these checks will cause CI to fail.**

#### Required Checks (Must Run ALL Before Committing)

**1. Linting & Formatting (MANDATORY)**
   - Python: `ruff check . && ruff format .` (apps/golf-api, apps/handicap-calculator)
   - TypeScript: `npm run lint && npm run format` (apps/golf-ui)
   - All style issues must be resolved (Google Style Guide)
   - See [Code Style & Linting](#code-style--linting) section above

**2. Type Checking (MANDATORY)**
   - Python: `pyright .` must pass with no errors (apps/golf-api, apps/handicap-calculator)
   - TypeScript: Full TypeScript (no `any` types without justification, verified via eslint)

**3. Tests (MANDATORY)**
   - Python: `pytest --cov=app --cov-fail-under=80` (apps/golf-api, apps/handicap-calculator)
   - TypeScript: `npm run test:ci` (apps/golf-ui)
   - **Minimum 80% test coverage required** across all services
   - All tests must pass before committing

#### Complete Pre-Commit Command Examples

**For Backend Changes (apps/golf-api):**
```bash
cd apps/golf-api
ruff format .
ruff check .
pyright .
pytest --cov=src/golf_api --cov-fail-under=80
# ALL commands must pass before committing
```

**For Backend Changes (apps/handicap-calculator):**
```bash
cd apps/handicap-calculator
ruff format .
ruff check .
pyright .
pytest --cov=src/handicap_calculator --cov-fail-under=80
# ALL commands must pass before committing
```

**For Frontend Changes (apps/golf-ui):**
```bash
cd apps/golf-ui
npm run lint
npm run format:check  # Or npm run format to auto-fix
npm test
# ALL commands must pass before committing
```

**⚠️ CRITICAL REMINDERS:**
- Run checks in the correct directory (cd to the service you modified)
- Run ALL checks, not just some of them
- Fix all errors before committing
- Never commit with failing checks
- Never skip checks to save time

### Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following [.github/copilot-instructions.md](.github/copilot-instructions.md)

3. **⚠️ MANDATORY: Run ALL pre-commit checks in the service directory:**

   **Backend example (apps/golf-api):**
   ```bash
   cd apps/golf-api
   ruff format .                           # Format
   ruff check .                            # Lint
   pyright .                               # Type check
   pytest --cov=src/golf_api --cov-fail-under=80  # Test
   ```

   **Backend example (apps/handicap-calculator):**
   ```bash
   cd apps/handicap-calculator
   ruff format .                           # Format
   ruff check .                            # Lint
   pyright .                               # Type check
   pytest --cov=src/handicap_calculator --cov-fail-under=80  # Test
   ```

   **Frontend example (apps/golf-ui):**
   ```bash
   cd apps/golf-ui
   npm run lint                            # Lint
   npm run format:check                    # Check format (or npm run format to auto-fix)
   npm test                                # Test
   ```

   **🚨 CRITICAL: ALL checks must pass with NO ERRORS before committing. This is NOT optional. CI will fail if you skip these checks.**

4. **Use conventional commit syntax:**
   ```
   type(scope): description

   Examples:
   - feat(members): add member search functionality
   - fix(api): return correct handicap on score updates
   - docs(readme): add custom domain setup instructions
   - test(matches): add edge case tests for match results
   - chore(deps): update FastAPI to 0.104.1
   ```

   Valid types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`

5. Submit a pull request with:
   - Clear description of what changed and why
   - Reference any related issues
   - Confirm all CI checks pass

### Release Management

Releases are managed automatically via **release-please**:
- Conventional commits determine version bumps (major/minor/patch)
- Release notes are generated from commit history
- GitHub Releases are created automatically
- No manual version number updates needed

See [CHANGELOG.md files](#) for release history.

## License

See [LICENSE](LICENSE) file for details.

## Support

For questions or issues, contact the club administrator or open an issue in this repository.
