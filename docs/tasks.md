# Development Tasks

This document breaks down the csocgolf-v2 application into small, achievable tasks organized by theme. Each task can be worked on by an AI agent or human developer and should be completable with a single PR.

**Task Complexity:** 🟢 Small (1-2 hours), 🟡 Medium (2-4 hours), 🔴 Large (4+ hours)

---

## Phase 1: Project Setup & Infrastructure

### 1.1 Initialize Node.js Frontend Project 🟢
**Apps:** `apps/golf-ui`
**Description:** Create the React + TypeScript + Vite project structure with necessary configuration.

**Acceptance Criteria:**
- [ ] Create `apps/golf-ui/` directory with package.json configured for React 19, TypeScript, Vite
- [ ] Add tsconfig.json with strict type checking enabled
- [ ] Add .env.example with VITE_API_BASE_URL and VITE_GOOGLE_CLIENT_ID
- [ ] Add .gitignore for Node.js
- [ ] Add ESLint config (Google TS style)
- [ ] Add Prettier config
- [ ] Add Vitest + @testing-library/react for testing
- [ ] Create empty `src/`, `tests/` directories
- [ ] Run `npm install` and verify all dependencies resolve
- [ ] Verify `npm run dev` works (shows Vite welcome page)
- [ ] Verify `npm run lint`, `npm run format`, `npm run test:ci` scripts work

**PR Size:** Small
**Resources:** vite.config.ts, tsconfig.json, package.json examples

---

### 1.2 Initialize Python Backend Project (golf-api) 🟢
**Apps:** `apps/golf-api`
**Description:** Create FastAPI project with pyproject.toml, project structure, and development setup.

**Acceptance Criteria:**
- [ ] Create `apps/golf-api/` directory structure (app/, tests/, Dockerfile, pyproject.toml)
- [ ] Configure pyproject.toml with FastAPI, Pydantic v2, Firebase Admin SDK, pytest dependencies
- [ ] Add ruff.toml with Google Python style config
- [ ] Create app/__init__.py and app/main.py with empty FastAPI app
- [ ] Add HTTP health check endpoint GET /health that returns {"status": "ok"}
- [ ] Create .env.example with required environment variables (GOOGLE_CLOUD_PROJECT, etc.)
- [ ] Create .gitignore for Python
- [ ] Add pytest.ini for test configuration
- [ ] Verify `pip install -e .` works
- [ ] Verify `uvicorn app.main:app --reload` starts server on port 8000
- [ ] Verify linting scripts work: `ruff check .`, `ruff format .`, `pyright .`
- [ ] Verify tests run: `pytest`

**PR Size:** Small
**Resources:** FastAPI docs, pyproject.toml template

---

### 1.3 Initialize Python Handicap Calculator Project 🟢
**Apps:** `apps/handicap-calculator`
**Description:** Create Pub/Sub subscriber service project structure.

**Acceptance Criteria:**
- [ ] Create `apps/handicap-calculator/` directory structure (app/, tests/, Dockerfile, pyproject.toml)
- [ ] Configure pyproject.toml with FastAPI, Pydantic v2, Firebase Admin SDK, Google Cloud Pub/Sub, pytest
- [ ] Create app/main.py with empty FastAPI app
- [ ] Add HTTP health check endpoint GET /health
- [ ] Create .env.example with Pub/Sub configuration
- [ ] Create .gitignore for Python
- [ ] Verify `pip install -e .` works
- [ ] Verify linting and tests run

**PR Size:** Small

---

### 1.4 Setup GitHub Actions CI/CD Pipeline 🟡
**Files:** `.github/workflows/`
**Description:** Create CI/CD workflow that runs linting, type checking, and tests on PR.

**Acceptance Criteria:**
- [ ] Create `.github/workflows/ci.yml` that:
  - Triggers on pull_request and push to main
  - Runs on ubuntu-latest
  - Sets up Node 20 and Python 3.12
  - Installs dependencies for all three apps
  - Runs linting: `ruff check`, `eslint`
  - Runs type checking: `pyright`, `tsc --noEmit`
  - Runs tests: `pytest --cov --cov-fail-under=80`, `npm run test:ci`
  - Fails if any step fails
- [ ] CI badge appears in README

**PR Size:** Small
**Resources:** GitHub Actions docs

---

## Phase 2: Database Schema & Firestore Setup

### 2.1 Define Firestore Collections (Documentation) 🟢
**Files:** `docs/firestore-schema.md`
**Description:** Document all Firestore collections, their fields, indexes, and access patterns.

**Acceptance Criteria:**
- [ ] Document users collection (userId, email, name, role, createdAt, lastLoginAt)
- [ ] Document members collection (memberId, firstName, lastName, email, phone, memberNo, initialHandicap, inactive, createdAt, updatedAt)
- [ ] Document clubs, courses, tees collections with proper relationships
- [ ] Document scores collection (memberId, teeId, date, handicap, scratch, nett, points, createdAt)
- [ ] Document matches collection (date, teeId, scoreIds[], winnerId, prizes[], createdAt, updatedAt)
- [ ] Document handicaps subcollection under members
- [ ] Show composite index requirements
- [ ] Include reasoning for denormalization choices

**PR Size:** Small

---

### 2.2 Create Firestore Service Wrapper (Backend) 🟡
**Apps:** `apps/golf-api`
**Files:** `app/services/firestore.py`
**Description:** Create service layer that wraps Firestore client with type-safe CRUD operations.

**Acceptance Criteria:**
- [ ] Create FirestoreService class with Firestore client initialization
- [ ] Add authentication: verify_id_token() using Firebase Admin SDK
- [ ] Add helper methods: get_user_role(), user_exists()
- [ ] Add error handling: DocumentNotFound, PermissionDenied, etc.
- [ ] Add structured logging with request IDs
- [ ] Write unit tests for Firestore operations
- [ ] Write integration tests with Firestore emulator
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 2.1

---

### 2.3 Create Pub/Sub Publisher Service (Backend) 🟡
**Apps:** `apps/golf-api`
**Files:** `app/services/pubsub.py`
**Description:** Create service for publishing score events to Pub/Sub topic.

**Acceptance Criteria:**
- [ ] Create PubSubService class with Pub/Sub client initialization
- [ ] Implement publish_score_event() that sends {event, memberId, scoreId, teeId, date, scratch, nett, timestamp}
- [ ] Add message validation
- [ ] Add error handling and retry logic
- [ ] Add structured logging
- [ ] Write unit tests with mocked Pub/Sub
- [ ] Achieve 80%+ coverage

**PR Size:** Medium

---

## Phase 3: Authentication & Authorization

### 3.1 Create Auth Middleware (Backend) 🟡
**Apps:** `apps/golf-api`
**Files:** `app/auth/middleware.py`, `app/auth/dependencies.py`
**Description:** Implement Google ID token verification and role-based access control.

**Acceptance Criteria:**
- [ ] Create middleware that extracts Bearer token from Authorization header
- [ ] Verify token using Firebase Admin SDK
- [ ] Handle expired/invalid tokens with 401 Unauthorized
- [ ] Extract user_id and email from decoded token
- [ ] Fetch user role from Firestore
- [ ] Create require_auth() dependency for protected endpoints
- [ ] Create require_admin() dependency for admin-only endpoints
- [ ] Add comprehensive error messages
- [ ] Write unit tests (mock Firebase, Firestore)
- [ ] Write integration tests with real tokens
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 2.2

---

### 3.2 Create Auth Context (Frontend) 🟡
**Apps:** `apps/golf-ui`
**Files:** `src/contexts/AuthContext.tsx`, `src/hooks/useAuth.ts`
**Description:** Implement Google OAuth integration and auth state management.

**Acceptance Criteria:**
- [ ] Create AuthContext with user state, loading, error
- [ ] Integrate Google Identity Services library
- [ ] Implement handleCredentialResponse() callback
- [ ] Store ID token in memory (NOT localStorage)
- [ ] Create useAuth() hook for consuming auth state
- [ ] Add logout functionality
- [ ] Handle token refresh
- [ ] Write comprehensive tests with MSW mocks
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Resources:** Google Identity Services docs

---

### 3.3 Create API Client with Auth Interceptor (Frontend) 🟢
**Apps:** `apps/golf-ui`
**Files:** `src/api/client.ts`
**Description:** Create Axios client that auto-injects auth tokens.

**Acceptance Criteria:**
- [ ] Create axios instance with baseURL from env
- [ ] Add request interceptor to inject Authorization header with ID token
- [ ] Add response interceptor to handle 401 Unauthorized
- [ ] Add response interceptor to handle 403 Forbidden
- [ ] Export configured client
- [ ] Write unit tests
- [ ] Achieve 80%+ coverage

**PR Size:** Small
**Dependencies:** 3.2

---

## Phase 4: Core API Endpoints

### 4.1 Create Member Routes (Backend) 🟡
**Apps:** `apps/golf-api`
**Files:** `app/routes/members.py`, `app/models.py`
**Description:** Implement member CRUD endpoints with Firestore integration.

**Endpoints:**
- `GET /api/v1/members` (list, paginated, public)
- `GET /api/v1/members/{id}` (view, public)
- `POST /api/v1/members` (create, admin only)
- `PUT /api/v1/members/{id}` (update, admin only)

**Acceptance Criteria:**
- [ ] Define Member, MemberCreate, MemberUpdate Pydantic models
- [ ] Implement list with pagination (page, page_size params)
- [ ] Implement get by ID with 404 handling
- [ ] Implement create with validation:
  - memberNo must be unique
  - email optional but unique if provided
  - initialHandicap optional
- [ ] Implement update with validation
- [ ] Implement delete (soft delete: set inactive=true)
- [ ] Add request/response examples
- [ ] Write comprehensive tests (unit + integration)
- [ ] Achieve 80%+ coverage
- [ ] All endpoints use auth middleware

**PR Size:** Medium
**Dependencies:** 2.2, 3.1

---

### 4.2 Create Score Routes (Backend) 🟡
**Apps:** `apps/golf-api`
**Files:** `app/routes/scores.py`
**Description:** Implement score recording and retrieval endpoints.

**Endpoints:**
- `POST /api/v1/scores` (create, admin only, triggers Pub/Sub)
- `GET /api/v1/members/{memberId}/scores` (list, public)
- `GET /api/v1/scores/{id}` (view, public)

**Acceptance Criteria:**
- [ ] Define Score Pydantic model
- [ ] Create endpoint validates:
  - memberId exists
  - teeId exists
  - date is valid
  - scratch and nett are positive
  - Returns early with 202 Accepted (handicap calculating async)
- [ ] Publish Pub/Sub event on score creation
- [ ] List endpoint supports pagination, filters
- [ ] Write comprehensive tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 2.2, 2.3, 3.1

---

### 4.3 Create Club/Course/Tee Routes (Backend) 🟡
**Apps:** `apps/golf-api`
**Files:** `app/routes/clubs.py` (or combined with courses/tees)
**Description:** Implement read-only endpoints for golf courses and tee information.

**Endpoints:**
- `GET /api/v1/clubs` (list)
- `GET /api/v1/clubs/{clubId}/courses` (list courses for club)
- `GET /api/v1/courses/{courseId}/tees` (list tees for course)

**Acceptance Criteria:**
- [ ] Define Club, Course, Tee Pydantic models
- [ ] All endpoints return with proper caching headers
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 2.2, 3.1

---

### 4.4 Create Match Routes (Backend) 🟡
**Apps:** `apps/golf-api`
**Files:** `app/routes/matches.py`
**Description:** Implement match creation and retrieval.

**Endpoints:**
- `GET /api/v1/matches` (list, paginated, public)
- `GET /api/v1/matches/{id}` (view, public)
- `POST /api/v1/matches` (create, admin only)

**Acceptance Criteria:**
- [ ] Define Match, MatchCreate Pydantic models
- [ ] Create validates:
  - teeId exists
  - scoreIds exist
  - date is valid
  - 2-26 players
  - prizes reference valid members
- [ ] List sorted by date descending
- [ ] Write comprehensive tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 2.2, 3.1, 4.1, 4.2

---

## Phase 5: Background Services

### 5.1 Create Handicap Calculation Service 🟡
**Apps:** `apps/handicap-calculator`
**Files:** `app/services/handicap.py`
**Description:** Implement Australian Golf handicap calculation logic.

**Acceptance Criteria:**
- [ ] Create calculate_handicap(scores: list[Score]) function
- [ ] Uses best-N-of-last-20 method per Australian standards:
  - <6 scores: best 1
  - 6-8: best 2
  - 9-11: best 3
  - 12-14: best 4
  - 15-16: best 5
  - 17-18: best 6
  - 19: best 7
  - 20+: best 8
- [ ] Apply 0.93 multiplier and round to 1 decimal
- [ ] Handle edge cases (0 scores, < 5 scores)
- [ ] Write comprehensive unit tests
- [ ] Achieve 80%+ coverage

**PR Size:** Small

---

### 5.2 Create Pub/Sub Subscriber (Handicap Calculator) 🟡
**Apps:** `apps/handicap-calculator`
**Files:** `app/services/pubsub.py`, `app/main.py` HTTP endpoint
**Description:** Listen to Pub/Sub score events and trigger handicap calculations.

**Acceptance Criteria:**
- [ ] Create Pub/Sub subscription handler
- [ ] Extract score event from Pub/Sub message
- [ ] Fetch member's last 20 scores from Firestore
- [ ] Calculate new handicap using 5.1
- [ ] Update member.handicap and member.handicapUpdatedAt in Firestore
- [ ] Log completion with request ID
- [ ] Handle errors gracefully (invalid scores, missing member, etc.)
- [ ] Implement exponential backoff for retries
- [ ] Create HTTP endpoint POST /calculate for manual trigger (testing)
- [ ] Write comprehensive tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 5.1, 2.2

---

## Phase 6: Frontend Components (Core)

### 6.1 Create Layout Components 🟢
**Apps:** `apps/golf-ui`
**Files:** `src/components/layout/Header.tsx`, `Footer.tsx`
**Description:** Create reusable header and footer components.

**Acceptance Criteria:**
- [ ] Header component with:
  - App logo/title
  - Navigation menu
  - User profile menu with logout
  - Responsive design (mobile hamburger)
- [ ] Footer component with:
  - Links to privacy policy, terms
  - Copyright notice
- [ ] Write component tests
- [ ] Achieve 80%+ coverage

**PR Size:** Small

---

### 6.2 Create Common UI Components 🟢
**Apps:** `apps/golf-ui`
**Files:** `src/components/common/Button.tsx`, `Card.tsx`, `Spinner.tsx`, etc.
**Description:** Create reusable UI building blocks.

**Acceptance Criteria:**
- [ ] Button component (primary, secondary, dangerous styles)
- [ ] Card component (container, spacing)
- [ ] Spinner/Loading component
- [ ] ErrorMessage component
- [ ] ConfirmDialog component
- [ ] All accessible (ARIA labels, keyboard support)
- [ ] Write component tests for each
- [ ] Achieve 80%+ coverage

**PR Size:** Small

---

### 6.3 Create Member List Component 🟡
**Apps:** `apps/golf-ui`
**Files:** `src/components/members/MemberList.tsx`, `src/hooks/useMembers.ts`
**Description:** Display paginated member list with search/filter.

**Acceptance Criteria:**
- [ ] Create useMembers() hook with TanStack Query
- [ ] Fetch from GET /api/v1/members with pagination
- [ ] Display members in table: Name, Member No, Email, Handicap
- [ ] Add pagination controls (prev/next, page number)
- [ ] Add loading spinners
- [ ] Add error handling with user messages
- [ ] Add inactive member filtering toggle
- [ ] Write component + hook tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 3.2, 3.3, 4.1, 6.2

---

### 6.4 Create Member Details Component 🟡
**Apps:** `apps/golf-ui`
**Files:** `src/components/members/MemberDetails.tsx`
**Description:** Display detailed member view with scores and handicap history.

**Acceptance Criteria:**
- [ ] Fetch member by ID
- [ ] Display member info (name, contact, stats)
- [ ] Display last 10 scores in a table
- [ ] Display handicap trend (chart or timeline)
- [ ] Add "Edit" button (admin only, hidden if member)
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 3.2, 4.1, 6.2

---

### 6.5 Create Score Details Component 🟡
**Apps:** `apps/golf-ui`
**Files:** `src/components/scores/ScoreCalculator.tsx`
**Description:** Create UI for recording/viewing score details.

**Acceptance Criteria:**
- [ ] Display score breakdown: scratch, nett, points
- [ ] Show handicap tag (member handicap at time of score)
- [ ] Show course/tee information
- [ ] Show date
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Small

---

## Phase 7: Frontend Pages & Routing

### 7.1 Create React Router Setup 🟢
**Apps:** `apps/golf-ui`
**Files:** `src/App.tsx`, routing configuration
**Description:** Setup React Router with all routes.

**Acceptance Criteria:**
- [ ] Create router with routes:
  - `/` – Home page
  - `/members` – Members list
  - `/members/:id` – Member details
  - `/matches` – Matches list
  - `/matches/:id` – Match details
  - `/admin/add-score` – Score recording (admin)
  - `/admin/add-member` – Member creation (admin)
  - `/*` – 404 Not Found
- [ ] Protected routes redirect to home if not authenticated
- [ ] Admin routes redirect if not admin
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Small
**Dependencies:** 3.2, 6.1

---

### 7.2 Create Home Page 🟢
**Apps:** `apps/golf-ui`
**Files:** `src/pages/HomePage.tsx`
**Description:** Create landing page with recent matches and member stats.

**Acceptance Criteria:**
- [ ] Display welcome message
- [ ] Show recent matches (last 5)
- [ ] Show top players by handicap
- [ ] Show login prompt if not authenticated
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Small
**Dependencies:** 3.2, 6.2, 7.1

---

### 7.3 Create Members Page 🟢
**Apps:** `apps/golf-ui`
**Files:** `src/pages/MembersPage.tsx`
**Description:** Page that uses MemberList component.

**Acceptance Criteria:**
- [ ] Render MemberList component
- [ ] Add "Add Member" button (admin)
- [ ] Link to member details on click
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Small
**Dependencies:** 3.2, 6.3, 7.1

---

### 7.4 Create Matches Page 🟡
**Apps:** `apps/golf-ui`
**Files:** `src/pages/MatchesPage.tsx`, hook for matches list
**Description:** Display paginated match list with details.

**Acceptance Criteria:**
- [ ] Create useMatches() hook with TanStack Query
- [ ] List matches: Date, Players, Winner
- [ ] Pagination
- [ ] Link to match details
- [ ] Add "Record Match" button (admin)
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 3.2, 4.4, 7.1

---

## Phase 8: Admin Features

### 8.1 Create Add Member Form 🟡
**Apps:** `apps/golf-ui`
**Files:** `src/components/members/AddMemberForm.tsx`, mutation hook
**Description:** Form for admins to add new members.

**Acceptance Criteria:**
- [ ] Create useCreateMember() mutation hook
- [ ] Form fields: First Name, Last Name, Email, Phone, Member No, Initial Handicap
- [ ] Validation (required fields, unique member no)
- [ ] Error handling
- [ ] Success toast/redirect
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 3.2, 4.1

---

### 8.2 Create Add Score Form 🟡
**Apps:** `apps/golf-ui`
**Files:** `src/components/scores/AddScoreForm.tsx`, mutation hook
**Description:** Form for admins to record score results.

**Acceptance Criteria:**
- [ ] Create useCreateScore() mutation hook
- [ ] Form fields: Member, Tee, Date, Scratch Score, Nett Score
- [ ] Validation
- [ ] Fetch member list and tee list for dropdowns
- [ ] Show "Handicap calculating..." message while Pub/Sub processes
- [ ] Success message
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Medium
**Dependencies:** 3.2, 2.3, 4.2, 4.3

---

### 8.3 Create Record Match Form 🔴
**Apps:** `apps/golf-ui`
**Files:** `src/components/matches/RecordMatchForm.tsx`, mutation hook
**Description:** Multi-step form to record match results with prizes.

**Acceptance Criteria:**
- [ ] Create useCreateMatch() mutation hook
- [ ] Step 1: Select tee, date
- [ ] Step 2: Add/select players and their scores
- [ ] Step 3: Assign prizes (nearest pin, longest drive, etc.)
- [ ] Validation at each step
- [ ] Fetch existing courses/tees
- [ ] POST to /api/v1/matches
- [ ] Success redirect to match details
- [ ] Write tests
- [ ] Achieve 80%+ coverage

**PR Size:** Large
**Dependencies:** 3.2, 4.3, 4.4

---

## Phase 9: Polish & Deployment

### 9.1 Create Dockerfile for Frontend 🟢
**Apps:** `apps/golf-ui`
**Files:** `Dockerfile`
**Description:** Build container for frontend (multi-stage build).

**Acceptance Criteria:**
- [ ] Stage 1: Build stage (Node 20, npm install, npm run build)
- [ ] Stage 2: Serve stage (minimal image, copy dist/)
- [ ] Expose port 3000
- [ ] Test build locally

**PR Size:** Small

---

### 9.2 Create Dockerfile for Backend 🟢
**Apps:** `apps/golf-api`
**Files:** `Dockerfile`
**Description:** Build container for FastAPI backend.

**Acceptance Criteria:**
- [ ] Base: python:3.12-slim
- [ ] Install dependencies from pyproject.toml
- [ ] Copy app/
- [ ] Expose port 8000
- [ ] CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000
- [ ] Test build locally

**PR Size:** Small

---

### 9.3 Create Dockerfile for Handicap Calculator 🟢
**Apps:** `apps/handicap-calculator`
**Files:** `Dockerfile`
**Description:** Build container for Pub/Sub subscriber.

**Acceptance Criteria:**
- [ ] Same as backend (9.2)
- [ ] Expose port 8001
- [ ] CMD: uvicorn app.main:app --host 0.0.0.0 --port 8001

**PR Size:** Small

---

### 9.4 Setup Cloud Run Deployment Script 🟡
**Files:** `scripts/deploy.sh`
**Description:** Script to build and deploy all services to Cloud Run.

**Acceptance Criteria:**
- [ ] Build frontend: `npm run build`, upload to Cloud Storage
- [ ] Build backend: docker build, push to Artifact Registry, deploy to Cloud Run
- [ ] Build calculator: docker build, push to Artifact Registry, deploy to Cloud Run
- [ ] Set environment variables from Secret Manager
- [ ] Script is idempotent (safe to run multiple times)
- [ ] Script handles errors gracefully

**PR Size:** Medium

---

### 9.5 Setup Cloud Storage Frontend Hosting 🟡
**Files:** `scripts/setup-frontend-hosting.sh`
**Description:** Configure Cloud Storage bucket for static SPA hosting.

**Acceptance Criteria:**
- [ ] Create bucket with custom domain name
- [ ] Enable static website hosting (index.html)
- [ ] Configure CORS for API domain
- [ ] Setup DNS CNAME
- [ ] Verify domain ownership
- [ ] Script documents all steps

**PR Size:** Medium

---

### 9.6 Add Comprehensive README.md Badges & Links 🟢
**Files:** `README.md`
**Description:** Add deployment links, badges, and getting started guide updates.

**Acceptance Criteria:**
- [ ] Add deployment URLs (API, Frontend)
- [ ] Add badges for build status
- [ ] Add link to architecture docs
- [ ] Add quick start for local development
- [ ] Add link to TASKS.md

**PR Size:** Small

---

### 9.7 Setup Monitoring & Logging 🟡
**Files:** `apps/golf-api/app/utils/logging.py`, `apps/handicap-calculator/app/utils/logging.py`
**Description:** Configure structured logging for Cloud Logging integration.

**Acceptance Criteria:**
- [ ] Setup JSON structured logging
- [ ] Include request ID in all logs
- [ ] Setup Cloud Logging client
- [ ] Add log level configuration
- [ ] Write tests

**PR Size:** Medium

---

## Phase 10: Documentation & Testing Enhancements

### 10.1 Add Comprehensive API Documentation 🟢
**Files:** FastAPI auto-generated docs + docs/api.md
**Description:** Document all API endpoints with examples.

**Acceptance Criteria:**
- [ ] FastAPI /docs endpoint is fully populated
- [ ] API endpoints have docstrings with:
  - Description
  - Request/response examples
  - Error codes
- [ ] docs/api.md has reference table of all endpoints
- [ ] Examples include curl commands

**PR Size:** Small

---

### 10.2 Add Frontend Component Storybook 🟡
**Apps:** `apps/golf-ui`
**Description:** Create Storybook for component documentation and testing.

**Acceptance Criteria:**
- [ ] Setup Storybook
- [ ] Add stories for all common components
- [ ] Add stories for page components
- [ ] Deploy Storybook to static host
- [ ] Document in README

**PR Size:** Medium

---

### 10.3 Add E2E Tests with Playwright 🟡
**Files:** `tests/e2e/`
**Description:** Create end-to-end tests for critical user flows.

**Acceptance Criteria:**
- [ ] Setup Playwright
- [ ] Test: Login flow
- [ ] Test: View member list and details
- [ ] Test: View match list and details
- [ ] Test: (Admin) Add member
- [ ] Test: (Admin) Record score
- [ ] Tests run against staging environment
- [ ] 80%+ coverage of critical paths

**PR Size:** Large

---

### 10.4 Add Load Testing & Performance Benchmarks 🟡
**Files:** `tests/load/`, `docs/performance.md`
**Description:** Test performance under load.

**Acceptance Criteria:**
- [ ] Setup k6 or similar load testing tool
- [ ] Test API endpoints: list members, view member, list matches
- [ ] Run 100 concurrent users for 5 minutes
- [ ] Document response times and throughput
- [ ] Verify stays within free tier quotas
- [ ] Document bottlenecks and optimization opportunities

**PR Size:** Medium

---

## Phase 11: Future Enhancements & Maintenance

### 11.1 Add Member Statistics Dashboard 🟡
**Apps:** `apps/golf-ui`
**Description:** Display player stats: average handicap, recent form, tournament wins.

**Acceptance Criteria:**
- [ ] New page /stats
- [ ] Show per-player stats table
- [ ] Link to player details
- [ ] Responsive design

**PR Size:** Medium

---

### 11.2 Add Handicap Tracker Chart 🟡
**Apps:** `apps/golf-ui`
**Description:** Visual handicap trend chart for members.

**Acceptance Criteria:**
- [ ] Use Chart.js or Recharts
- [ ] Display member's handicap over time
- [ ] Show improving/declining trend

**PR Size:** Medium

---

### 11.3 Add Search & Filter Features 🟡
**Apps:** `apps/golf-ui`
**Description:** Add search and advanced filtering across pages.

**Acceptance Criteria:**
- [ ] Member search by name/email
- [ ] Filter members by handicap range
- [ ] Filter matches by date range
- [ ] Save filter preferences

**PR Size:** Medium

---

### 11.4 Add Mobile App (React Native) 🔴
**Apps:** `apps/mobile`
**Description:** Create cross-platform mobile app.

**Acceptance Criteria:**
- [ ] Share API client/types with web
- [ ] Core flows: login, view members, view matches
- [ ] iOS and Android builds
- [ ] Distribution via App Store/Play Store

**PR Size:** Very Large
**Dependencies:** All previous phases

---

## Task Completion Guidelines

### Before Starting a Task:
1. ✅ Read the acceptance criteria carefully
2. ✅ Identify dependencies (must be completed first)
3. ✅ Review the architecture docs for context
4. ✅ Check existing code patterns in `.github/copilot-instructions.md`

### During Development:
1. ✅ Write code following Google Style Guide
2. ✅ Add comprehensive unit tests (80%+ coverage minimum)
3. ✅ Run linting before committing: `ruff check`, `eslint`
4. ✅ Run type checking: `pyright`, `tsc --noEmit`
5. ✅ Format code: `ruff format`, `prettier`

### Before Submitting PR:
1. ✅ All tests pass: `pytest --cov --cov-fail-under=80`, `npm run test:ci`
2. ✅ All linting passes
3. ✅ All type checking passes
4. ✅ Use conventional commit syntax (e.g., `feat(members): add member list API`)
5. ✅ Write clear PR description with context
6. ✅ Request review and address feedback

### After PR Merge:
1. ✅ Verify CI/CD pipeline passes
2. ✅ Update any dependent task documentation
3. ✅ Celebrate! ✨

---

## Tracking Progress

Use GitHub Projects or Issues to track task status:
- [ ] Not Started
- [ ] In Progress
- [ ] Review/Testing
- [ ] Completed

Mark tasks as "good for first contribution" if suitable for new contributors.
