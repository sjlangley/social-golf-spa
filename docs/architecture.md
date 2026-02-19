# Architecture Documentation

## Context & Goals

This document describes the target architecture for the rearchitected Caringbah Social Golf Club management system. This is a **v2 reimplementation** that migrates from a Flask + FastAPI monolith with MongoDB to a modern SPA + Cloud Run + Firestore stack, **optimized for free-tier GCP deployment**.

### Why Rearchitect?

**Original System Constraints:**
- Server-side rendering (Jinja2 templates) limits interactivity
- MongoDB requires managing replica sets and infrastructure
- Docker Compose deployment lacks auto-scaling and managed infrastructure
- Mixed Flask/FastAPI creates complexity
- Limited observability and monitoring

**Target Goals:**
- Modern, responsive SPA user experience
- Serverless backend (lower ops burden, auto-scaling)
- Managed database (Firestore) with better GCP integration
- Clear separation between frontend and backend
- Production-grade auth with Google Identity
- Cloud-native logging and monitoring
- **Free-tier cost optimization** (zero-scale Cloud Run, Cloud Storage-served frontend)
- **Asynchronous handicap calculation** via Pub/Sub to avoid slow API responses

## Existing System Snapshot

### Current Architecture (v1)
**Tech Stack:**
- **Frontend:** Flask with Jinja2 templates (server-side rendering)
- **Backend:** FastAPI with REST + GraphQL (Strawberry)
- **Database:** MongoDB 8.2.3 with replica set
- **Cache:** Memcached
- **Auth:** Google OAuth 2.0 via Flask-Login (server-side session)
- **Deployment:** Docker Compose
- **Reverse Proxy:** nginx
- **CI/CD:** GitHub Actions (pytest, ruff, pylint, jest, selenium)

**Data Model:**
- `members` – Player profiles (name, email, phone, initial handicap)
- `clubs` – Golf clubs
- `courses` – Golf courses (linked to clubs)
- `tees` – Tee boxes (linked to courses, includes par/slope/AMCR)
- `scores` – Individual round scores (member, tee, date, handicap, scratch, nett, points)
- `matches` – Match results (date, tee, scores[], winners, prizes)
- `handicaps` – Handicap history (member, handicap, date)
- `users` – OAuth user records (for authentication)

**Key Features:**
1. Member management (list, view details, add)
2. Score tracking with automatic handicap calc (Australian Golf standards)
3. Match result recording (up to 26 players, prizes)
4. Club/course/tee information management
5. Handicap calculation using best-8-of-20 scores method
6. Prize tracking (nearest pin, longest drive, drive & chip)

**Access Patterns:**
- Public: List members, view member details, view matches, browse clubs
- Authenticated: Add members, record match results
- No multi-tenancy (single-club instance)
- No role-based access control (all authenticated users are admins)

**User Personas:**
1. **Public Visitors** – View member list, stats, match results
2. **Club Administrators** – Record scores/matches, manage members

**Current Pain Points:**
- Server-rendered pages feel dated
- No real-time updates without page refresh
- MongoDB ops overhead (backups, replica sets, monitoring)
- Mixed framework adds complexity
- Limited mobile experience
- Session-based auth doesn't scale well

## Target Architecture

### High-Level Design (Free-Tier Optimized)

```
┌─────────────────────────────────────────┐
│      React SPA (Node.js + Vite)         │
│  • Served from Cloud Storage bucket      │
│  • TanStack Query (data fetching)        │
│  • React Router (routing)                │
│  • Google Identity Services (auth)       │
│                                          │
│  Free Tier: Cloud Storage + Cloud CDN   │
└──────────────┬────────────────────────────┘
               │
               │ HTTPS
               │ Authorization: Bearer <ID_TOKEN>
               │
               ▼
┌─────────────────────────────────────────┐
│      FastAPI Backend (Cloud Run)         │
│  • Google ID Token verification          │
│  • REST API (/api/v1/*)                  │
│  • Publishes score events to Pub/Sub     │
│  • Role-based authorization              │
│  • Request ID middleware                 │
│  • Structured JSON logging               │
│                                          │
│  Free Tier: min=0, auto-scales to zero   │
│  • Request timeout: 300s                 │
└──────────────┬──────────────────┬────────┘
               │                  │
               │ Firestore API    │ Pub/Sub (score.created)
               │                  │
               ▼                  ▼
    ┌──────────────────┐  ┌────────────────────────────┐
    │    Firestore     │  │ Handicap Calculator        │
    │ • Collections    │  │ (Cloud Run Service)        │
    │ • Free domain    │  │ • Subscribes to Pub/Sub    │
    │ • 50K reads/day  │  │ • Calculates handicaps     │
    │ • 20K writes/day │  │ • Writes to Firestore      │
    │ • 20K deletes    │  │ • Free tier: min=0         │
    └──────────────────┘  └────────────────────────────┘
```

### Component Responsibilities

#### Frontend (React SPA)
**Technology:** React 19, TypeScript, Vite, TanStack Query, React Router

**Deployment (Free Tier):**
- Built as static assets with `npm run build`
- Uploaded to Cloud Storage bucket (single origin)
- Served directly from Cloud Storage (no Cloud CDN to reduce costs)
- Served from custom domain (e.g., `csocgolf.com`) via Cloud Storage static hosting
- HTTPS enabled automatically via Google-managed SSL certificate
- Configured for CORS from API domain only

**Custom Domain Setup:**
```bash
# 1. Create Cloud Storage bucket with custom domain name
gsutil mb gs://csocgolf.com

# 2. Configure bucket for static website hosting
gsutil web set -m index.html gs://csocgolf.com

# 3. Set DNS CNAME record to point to Cloud Storage
# In your DNS provider (Route53, Cloudflare, GCP Cloud DNS, etc.):
# CNAME: csocgolf.com -> c.storage.googleapis.com
# (or c2.storage.googleapis.com for verification)

# 4. Verify domain ownership via Cloud Console

# 5. Google automatically provisions SSL certificate (cert ready in ~15 minutes)

# 6. Upload built frontend assets
gsutil -m cp -r dist/* gs://csocgolf.com/
```

**Why Cloud Storage for Frontend?**
- 5 GB free storage (sufficient for static SPA)
- No compute costs (unlike Cloud Run)
- Custom domain support with automatic HTTPS
- No CDN costs (direct Cloud Storage serving is free)
- Easy deployment: just upload built assets
- Global distribution via Cloud Storage's edge nodes

**Responsibilities:**
- Render all UI components
- Handle client-side routing
- Manage application state
- Obtain Google ID token via Google Identity Services
- Send authenticated requests to backend with ID token in `Authorization: Bearer <token>` header
- Cache API responses with TanStack Query
- Display error states and loading indicators
- Handle "handicap calculating" UI state while calculation happens asynchronously

**Does NOT:**
- Directly access Firestore (all data through backend API)
- Validate authorization (backend enforces all access control)
- Store sensitive data (only ID token in memory, no localStorage for tokens)
- Serve any backend logic

#### Backend (FastAPI on Cloud Run)
**Technology:** FastAPI, Python 3.12, Firebase Admin SDK, Pydantic v2

**Responsibilities:**
- Verify Google ID tokens on every protected request
- Extract user identity from verified token
- Enforce role-based authorization (check user role from Firestore)
- Validate scores and match data
- Interface with Firestore (CRUD operations)
- **Publish score events to Pub/Sub** (instead of calculating handicaps)
- Return structured JSON responses (with "handicap_calculating" status)
- Log all requests with structured JSON (including request IDs)
- Handle errors gracefully with consistent error responses

**Does NOT:**
- Calculate handicaps (delegated to Pub/Sub subscriber)
- Maintain sessions (stateless)
- Store user credentials (delegated to Google)
- Serve static files (frontend is separate)

**Scaling (Free Tier):**
- Cloud Run: min=0 instances, max=10 (within free tier limits)
- Auto-scales based on request volume
- Each instance is stateless
- No shared state between instances (Firestore is source of truth)
- Free tier includes ~2 million requests/month

**Deployment:**
- Build Docker image
- Push to Artifact Registry
- Deploy to Cloud Run with service account
- Environment variables via Secret Manager or .env
- No cost: stays in free tier with low traffic (<2M requests/month)

#### Database (Firestore)
**Mode:** Native mode (not Datastore mode)

**Why Firestore over MongoDB:**
- Fully managed (no replica sets, no ops burden)
- Native GCP integration (IAM, VPC, logging)
- Real-time capabilities (future feature)
- Automatic scaling and replication
- Strong consistency with multi-region support
- Better cost model for our scale (low read/write volume)

**Collections & Schema:**

```typescript
// users collection (for auth & authorization)
users/{userId}
  email: string
  name: string
  profilePic: string
  role: "admin" | "member"  // authorization role
  createdAt: timestamp
  lastLoginAt: timestamp

// members collection (club members)
members/{memberId}
  firstName: string
  lastName: string
  nickName?: string
  email?: string
  phone?: string[]
  memberNo: number
  initialHandicap?: number
  inactive: boolean
  createdAt: timestamp
  updatedAt: timestamp

// clubs collection
clubs/{clubId}
  name: string
  createdAt: timestamp
  updatedAt: timestamp

// courses collection
courses/{courseId}
  name: string
  clubId: string  // reference to clubs/{clubId}
  prizes: Array<{name: string, type: "nearest_pin" | "longest_drive" | "drive_and_chip"}>
  createdAt: timestamp
  updatedAt: timestamp

// tees collection
tees/{teeId}
  name: string
  courseId: string  // reference to courses/{courseId}
  par: number
  slope: number
  amcr: number  // Australian Men's Course Rating
  distance?: number
  createdAt: timestamp
  updatedAt: timestamp

// scores collection
scores/{scoreId}
  memberId: string  // reference to members/{memberId}
  teeId: string  // reference to tees/{teeId}
  date: timestamp
  handicap?: number
  scratch: number  // gross score
  nett: number  // net score
  points?: number  // Stableford points
  createdAt: timestamp

// matches collection
matches/{matchId}
  date: timestamp
  teeId: string  // reference to tees/{teeId}
  scoreIds: string[]  // references to scores/{scoreId}
  winnerId?: string  // reference to members/{memberId}
  runnerUpId?: string
  thirdPlaceId?: string
  fourthPlaceId?: string
  prizes: Array<{
    memberId?: string,
    name: string,
    type: "nearest_pin" | "longest_drive" | "drive_and_chip"
  }>
  createdAt: timestamp
  updatedAt: timestamp

// handicaps collection
handicaps/{handicapId}
  memberId: string  // reference to members/{memberId}
  handicap: number
  date: timestamp
  createdAt: timestamp
```

**Indexes Required:**
```
// Composite indexes for common queries
members: (inactive, memberNo)
scores: (memberId, date DESC)
matches: (date DESC)
handicaps: (memberId, date DESC)
courses: (clubId, createdAt)
tees: (courseId, createdAt)
```

**Query Patterns:**
- List active members sorted by member number
- Get all scores for a member, sorted by date descending
- Get recent matches (paginated)
- Get handicap history for a member
- Get courses for a club
- Get tees for a course

#### Pub/Sub Topic: `score.created`

Topics enable asynchronous processing while keeping the main API fast.

**Publisher (Main Backend):**
When a score is created, the backend publishes a message immediately after writing to Firestore:
```python
message_data = {
    'memberId': score.memberId,
    'scoreId': score.id,
    'timestamp': time.time(),
}

publisher.publish(
    topic_path,
    json.dumps(message_data).encode('utf-8'),
    # Optional attributes for filtering/routing
    messageType='score.created'
)

# Respond to user immediately
return {'status': 'created', 'data': score, 'handicap_status': 'calculating'}
```

**Subscriber (Handicap Calculator Service):**
A separate Cloud Run service listens on the Pub/Sub subscription with a push endpoint. When a message arrives:

1. Extract `memberId` from message
2. Fetch all scores for that member from Firestore (sorted by date)
3. Calculate new handicap using Australian Golf standards
4. Write to `handicaps/{memberId}` collection
5. Acknowledge message to mark as processed

If processing fails, Pub/Sub automatically retries with exponential backoff.

**Benefits:**
- **Fast API responses** – Backend doesn't wait for handicap calculation
- **Decoupled services** – Frontend, API, and calculator are independent
- **Auto-scaling** – Pub/Sub and Calculator service both scale independently
- **Retry logic** – Built-in failure handling and retries
- **Free tier** – Pub/Sub is free up to 10 GB/month (plenty for our volume)

**Why Free Tier Friendly:**
- Main API stays responsive (no time-consuming calculations)
- Calculator service scales to zero when idle
- Pub/Sub messages are tiny (just memberId, no calculation)
- ~100 messages/month (one per score) = negligible cost

#### Database (Firestore)

**Why Firestore over MongoDB?**
- **Fully managed** (no replica sets, no ops burden)
- **Native GCP integration** (IAM, VPC, logging)
- **Free tier is generous:**
  - 50K reads/day
  - 20K writes/day
  - 20K deletes/day
  - Sufficient for a golf club (< 100 members, < 50 API calls/day)
- **Real-time capabilities** (future feature)
- **Strong consistency** with multi-region support
- **Better cost model** for our scale (no minimum)

**Mode:** Native mode (not Datastore mode)

## Custom Domain & HTTPS

### Static SPA Hosting with Custom Domain

The React SPA is served from a Cloud Storage bucket configured with a custom domain, providing free HTTPS and global distribution.

**Why This Approach?**
- **No compute costs** – Cloud Storage is storage-only, no per-request charges
- **Automatic HTTPS** – Google provisions and manages SSL certificates
- **Custom branded domain** – Serve from `csocgolf.com` instead of storage URLs
- **Global distribution** – Cloud Storage has edge nodes worldwide
- **Free tier friendly** – 5 GB storage is more than enough for SPA

**DNS Configuration:**

The domain points to Cloud Storage via CNAME record:
```
csocgolf.com  CNAME  c.storage.googleapis.com
```

(Alternative: `c2.storage.googleapis.com` for redundancy)

**HTTPS/SSL Setup:**

Google Cloud automatically provisions a managed SSL certificate:
1. Domain must be verified (simple TXT or CNAME record check)
2. Certificate provisioned automatically (~15 minutes)
3. Certificate auto-renewed (no action needed)
4. HTTPS enforced (HTTP redirects to HTTPS)

**CORS Configuration:**

The bucket is configured to allow API calls from the API domain:
```json
[
  {
    "origin": ["https://api.csocgolf.com"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
```

**Bucket Structure:**

```
gs://csocgolf.com/
├── index.html          (SPA entry point)
├── style-*.css         (built styles)
├── main-*.js           (bundled JavaScript)
├── assets/
│   ├── images/
│   ├── fonts/
│   └── ...
└── # All files served with appropriate Cache-Control headers
```

**Cost Breakdown (Monthly):**
- Cloud Storage: ~$0.02 (within 5 GB free tier)
- Custom SSL: $0 (Google-managed)
- Data egress: $0 (first 1 GB free, then charges apply for large volumes)
- **Total: Free or <$1/month** depending on traffic

## Authentication & Authorization

### Authentication Flow

**1. Frontend Obtains ID Token:**
```javascript
// User clicks "Sign in with Google"
// Google Identity Services handles OAuth flow
// Frontend receives ID token (JWT)
const credential = response.credential; // ID token

// Include in all API requests
fetch('https://api.csocgolf.com/api/v1/members', {
  headers: {
    'Authorization': `Bearer ${credential}`
  }
});
```

**2. Backend Verifies Token:**
```python
from firebase_admin import auth

async def verify_token(token: str) -> dict:
    """Verify Google ID token and return decoded claims."""
    try:
        # Firebase Admin SDK verifies:
        # - Signature (using Google's public keys)
        # - Expiration (exp claim)
        # - Audience (matches our Google Client ID)
        # - Issuer (accounts.google.com)
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**3. Backend Extracts User Info:**
```python
user_id = decoded_token['sub']  # Google user ID
email = decoded_token['email']
email_verified = decoded_token.get('email_verified', False)

# Lookup user in Firestore to get role
user_doc = firestore_client.collection('users').document(user_id).get()
user_role = user_doc.get('role') if user_doc.exists else 'member'
```

### Authorization Model

**Roles:**
- `admin` – Can create/update/delete members, matches, scores
- `member` – Read-only access (view members, matches, scores)

**Role Assignment:**
- First user to log in is automatically assigned `admin` role
- Subsequent users default to `member` role
- Admins can promote other users to `admin` via an admin UI

**Enforcement:**
Backend checks role on every protected endpoint:
```python
@router.post("/members", dependencies=[Depends(require_admin)])
async def create_member(member: Member, user: AuthUser = Depends(get_current_user)):
    # Only admins can create members
    ...

@router.get("/members")
async def list_members(user: AuthUser = Depends(get_current_user_optional)):
    # Anyone (even unauthenticated) can list members
    ...
```

**Security Principles:**
- **Never trust frontend** – Always verify token and check role on backend
- **Token in Authorization header only** – Not in query params or cookies
- **Short-lived tokens** – Google ID tokens expire after 1 hour
- **No token storage in localStorage** – Keep in memory only
- **HTTPS only** – All traffic encrypted in transit

## API Design Conventions

### Versioning
All API endpoints are prefixed with `/api/v1/` to allow future versioning.

Example: `GET /api/v1/members`

### Standard Responses

**Success (200 OK):**
```json
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

**Created (201 Created):**
```json
{
  "data": {...},
  "id": "abc123"
}
```

**Error (4xx/5xx):**
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "First name is required",
    "details": {
      "field": "firstName"
    },
    "requestId": "req_123abc"
  }
}
```

### Pagination
List endpoints support pagination via query params:
- `?page=1` (default: 1)
- `?pageSize=20` (default: 20, max: 100)

Response includes pagination metadata:
```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 2,
    "pageSize": 20,
    "hasMore": true
  }
}
```

### Error Codes
- `AUTHENTICATION_REQUIRED` – Missing or invalid token
- `PERMISSION_DENIED` – User lacks required role
- `NOT_FOUND` – Resource doesn't exist
- `INVALID_INPUT` – Validation error
- `CONFLICT` – Resource conflict (e.g., duplicate member)
- `INTERNAL_ERROR` – Unexpected server error

### Request IDs
Every request generates a unique ID for tracing:
- Returned in response header: `X-Request-ID: req_123abc`
- Included in error responses
- Logged with all backend logs for correlation

## Observability

### Structured Logging
All logs are JSON formatted for Cloud Logging:
```json
{
  "timestamp": "2026-02-19T10:30:00.000Z",
  "severity": "INFO",
  "requestId": "req_123abc",
  "user": "user@example.com",
  "method": "POST",
  "path": "/api/v1/members",
  "duration": 45,
  "status": 201
}
```

**Log Levels:**
- `DEBUG` – Development/troubleshooting (not in production)
- `INFO` – Normal operations (requests, actions)
- `WARNING` – Unexpected but handled (invalid input, rate limits)
- `ERROR` – Errors requiring attention (exceptions, failures)

### Request Tracing
- Request ID generated at ingress (Cloud Run or middleware)
- Passed through all internal calls
- Included in all logs and error responses
- Queryable in Cloud Logging for full request trace

### Metrics (via Cloud Run)
- Request count (by status code)
- Request latency (p50, p95, p99)
- Error rate
- Container instance count
- Cold start frequency

### Alerts (Future)
- Error rate > 5% for 5 minutes
- p95 latency > 2 seconds
- Zero healthy instances

## Security Posture

### CORS
Backend configures CORS to allow only the frontend domain:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://csocgolf.com"],  # Frontend domain
    allow_credentials=False,  # No cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Token Verification
- **Every** protected endpoint verifies the ID token
- Tokens verified using Firebase Admin SDK (checks signature, expiration, audience)
- Verification uses cached Google public keys (refreshed automatically)
- Failed verification returns 401 Unauthorized

### Authorization
- Role checked after authentication
- Unauthorized actions return 403 Forbidden
- All admin actions logged with user identity

### Input Validation
- Pydantic models validate all inputs
- SQL injection not applicable (Firestore is NoSQL)
- XSS prevented by React's default escaping

### Secret Management
- Secrets stored in GCP Secret Manager
- Never committed to git
- Accessed via service account in Cloud Run
- Rotated periodically

### Least Privilege
- Cloud Run service account has minimal permissions:
  - Firestore read/write
  - Secret Manager read
  - Cloud Logging write
- No external network access unless required

### Rate Limiting
- Cloud Armor (future) for DDoS protection
- Backend rate limiting per user (future):
  - 100 requests/minute per user
  - 1000 requests/hour per user

## CI/CD Pipeline

### CI (Continuous Integration)
**Trigger:** Pull request or push to `main`

**Backend Checks:**
1. Lint with `ruff`
2. Type check with `mypy`
3. Run unit tests with `pytest`
4. Generate coverage report (require >80%)

**Frontend Checks:**
1. Lint with ESLint
2. Type check with TypeScript compiler
3. Run unit tests with Vitest
4. Generate coverage report (require >80%)

**Workflow File:** `.github/workflows/ci.yml`

### CD (Continuous Deployment)
**Trigger:** Push to `main` (after CI passes)

**Backend Deployment:**
1. Build Docker image
2. Tag with git SHA and `latest`
3. Push to Artifact Registry
4. Deploy to Cloud Run (staging)
5. Run smoke tests
6. Promote to production (manual approval)

**Frontend Deployment:**
1. Install dependencies
2. Build static assets with `npm run build`
3. Upload to Cloud Storage (staging bucket)
4. Invalidate Cloud CDN cache
5. Run E2E tests against staging
6. Promote to production (manual approval)

**Workflow File:** `.github/workflows/deploy.yml`

### Environments
- **Staging** – Auto-deployed on merge to `main`
  - Backend: `https://staging-api.csocgolf.com`
  - Frontend: `https://staging.csocgolf.com`
  - Firestore: Separate staging database

- **Production** – Manual promotion after staging validation
  - Backend: `https://api.csocgolf.com`
  - Frontend: `https://csocgolf.com`
  - Firestore: Production database

## Data Migration Strategy

### Phase 1: Schema Mapping
Map MongoDB collections to Firestore collections:
- Preserve document IDs where possible
- Convert date strings to Firestore timestamps
- Convert embedded documents to maps
- Convert references (MongoDB ObjectId → Firestore document reference)

### Phase 2: Export from MongoDB
```bash
mongoexport --collection=members --out=members.json
# Repeat for all collections
```

### Phase 3: Transform & Load
Write Python script to:
1. Read JSON exports
2. Transform to Firestore schema
3. Use Firebase Admin SDK to batch write
4. Verify record counts match

### Phase 4: Validation
- Compare record counts
- Spot-check critical records (members, recent matches)
- Run test queries against new database

### Phase 5: Cutover
- Enable maintenance mode on old system
- Perform final incremental sync (if any changes)
- Update DNS to point to new frontend
- Monitor for errors

**Rollback Plan:**
- Keep old system running for 30 days
- If critical issues found, revert DNS to old system

## Open Questions

These items could not be determined from the existing codebase and need clarification:

1. **Production Hosting**
   - Where is the current system hosted in production?
   - What is the current domain name?
   - What is the current traffic volume (requests/day)?

2. **Authorization Scope**
   - Should all authenticated users be admins, or do we need a member role?
   - Are there different permission levels for different admin actions?
   - Should members be able to edit their own profile?

3. **Data Retention**
   - How long should we keep historical scores/matches?
   - Are there any compliance requirements (GDPR, data residency)?
   - Do we need audit logs for admin actions?

4. **Scalability**
   - How many members are expected (now and future)?
   - How many matches per year?
   - How many concurrent users during peak times?

5. **Multi-Tenancy**
   - Will the system ever need to support multiple clubs?
   - If yes, should we design for multi-tenancy now?

6. **Mobile App**
   - Is a native mobile app planned?
   - If yes, should backend support mobile tokens differently?

7. **Real-Time Features**
   - Would live leaderboard during a match be useful?
   - Should members receive notifications for new matches?

8. **Email Notifications**
   - Should members receive email summaries?
   - Match result notifications?
   - Handicap update notifications?

9. **Integration Points**
   - Integration with Australian Golf handicap systems?
   - Export to third-party golf platforms?
   - Calendar integration (iCal) for match dates?

10. **Budget & Cost**
    - What is the expected monthly budget for GCP services?
    - Is cost optimization a priority over feature velocity?

## Decision Log

### Why React over Vue/Angular?
- Larger ecosystem and community
- Better TypeScript support
- Team familiarity
- Excellent developer tooling (Vite)

### Why TanStack Query over Redux?
- Simpler for API data fetching
- Built-in caching and invalidation
- Less boilerplate
- Better fit for our read-heavy use case

### Why Firestore over Cloud SQL?
- Better GCP integration (IAM, logging)
- No SQL management overhead
- Real-time capabilities (future feature)
- Document model fits our data structure
- Cost-effective for our scale (< 1M reads/month)

### Why Cloud Run over Cloud Functions?
- Better for HTTP APIs (FastAPI support)
- More control over runtime environment
- Standard Docker deployment
- Cost-effective with scale-to-zero
- No cold start for low-concurrency functions

### Why Cloud Storage + CDN over Cloud Run for Frontend?
- Static assets don't need compute
- Global CDN distribution (better performance)
- Lower cost (storage vs. compute)
- Simpler deployment (just upload files)

### Why Keep FastAPI vs. Migrate to Node.js?
- FastAPI already in use and working well
- Excellent async performance
- Great OpenAPI/docs generation
- Team familiarity with Python
- Type safety with Pydantic
- No compelling reason to rewrite in Node.js

### Why Remove GraphQL?
- REST is simpler and sufficient for our needs
- GraphQL adds complexity (schema, resolvers)
- No complex nested queries required
- REST is more widely understood
- Easier to cache and rate limit

### Why Cloud Storage for Frontend Instead of Cloud Run?
- Static assets need no compute (costs would outweigh benefits)
- 5 GB free storage is more than enough
- No pay-per-request charges
- Simple deployment (just upload files)
- GCP serves from global edges automatically

### Why Pub/Sub for Handicap Calculation?
- **Decouples concerns** – API stays fast, calculation happens asynchronously
- **Free tier friendly** – Pub/Sub is free up to 10 GB/month
- **Automatic retries** – Messages retry on failure without code
- **Scales independently** – Calculator service scales only when needed
- **Simpler code** – Backend doesn't need complex handicap logic in request path
- **Better UX** – Users see quick response (\"calculating\" status), handicap updates in real-time

### Why Separate Handicap Calculator Service vs. Background Task?
- **Decoupled infrastructure** – Can restart without affecting API
- **Independent scaling** – Scales only for calculation load
- **Failure isolation** – Bad calculation doesn't crash API
- **Future extensibility** – Can replace or enhance without API changes
- **Monitoring** – Easy to track calculation performance separately

## Next Steps

### Phase 1: Setup GCP Project (Free Tier)
1. Create GCP project
2. Enable APIs:
   - Cloud Run (free tier: 2M requests/month)
   - Firestore (free tier: 50K reads/20K writes/day)
   - Pub/Sub (free tier: 10 GB/month)
   - Cloud Storage (free tier: 5 GB)
   - Cloud Build (free tier: 120 build-minutes/day)
   - Artifact Registry (free tier: with Cloud Build)
3. Create service accounts:
   - `main-api` (for FastAPI backend)
   - `handicap-calculator` (for Pub/Sub subscriber)
4. Configure OAuth consent screen and create credentials

### Phase 2: Setup Pub/Sub Infrastructure
1. Create Pub/Sub topic: `score.created`
2. Create Pub/Sub subscription: push-based to handicap calculator service
3. Configure dead-letter topic for failed messages (optional but recommended)
4. Setup IAM:
   - Grant `main-api` service account: Pub/Sub Publisher
   - Grant `handicap-calculator` service account: Pub/Sub Subscriber

### Phase 3: Implement Backend Skeleton
- FastAPI app structure
- Auth middleware (token verification)
- Firestore client initialization
- Pub/Sub publisher setup
- Health check endpoint
- Docker configuration
- Deploy to Cloud Run with `main-api` service account

### Phase 4: Implement Handicap Calculator Service
- Cloud Run service listening on HTTP for Pub/Sub push
- Pub/Sub message parsing
- Handicap calculation logic
- Firestore write (upsert handicap document)
- Error handling and dead-letter publishing
- Docker configuration
- Deploy to Cloud Run with `handicap-calculator` service account

### Phase 5: Implement Frontend Skeleton
- Vite + React + TypeScript setup
- Google Sign-In integration
- API client with auth headers
- Basic routing structure
- UI state for \"handicap calculating\" status
- Build static assets

### Phase 6: Implement Core Features
- **Backend:**
  - Member CRUD endpoints
  - Score recording (publishes to Pub/Sub)
  - Match result endpoints
  - Query endpoints (list members, get scores, etc.)
- **Frontend:**
  - Member list page
  - Score recording form
  - Match result entry
  - Member details page with handicap history
  - Real-time handicap status updates

### Phase 7: Upload Frontend to Cloud Storage with Custom Domain
1. **Create Cloud Storage bucket:**
   ```bash
   gsutil mb gs://csocgolf.com  # Use your domain name as bucket name
   ```

2. **Configure static website hosting:**
   ```bash
   gsutil web set -m index.html gs://csocgolf.com
   ```

3. **Setup custom domain DNS:**
   - In your DNS provider, create a CNAME record:
     - Hostname: `csocgolf.com` (or `www.csocgolf.com`)
     - Target: `c.storage.googleapis.com`
   - Alternatively, use `c2.storage.googleapis.com` for geo-redundancy

4. **Configure CORS policy** for API communication:
   ```bash
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

5. **Verify domain ownership** in Google Cloud Console:
   - Navigate to: Cloud Storage > Buckets > [bucket] > Configuration
   - Complete domain verification (takes ~5-15 minutes)

6. **Google provisions SSL certificate:**
   - Automatic HTTPS setup (Google-managed SSL)
   - Ready in ~15 minutes after verification
   - Automatic renewal

7. **Build and deploy frontend:**
   ```bash
   cd frontend
   npm run build
   gsutil -m cp -r dist/* gs://csocgolf.com/
   ```

8. **Set bucket permissions:**
   - Make bucket publicly readable (authenticated users already have access)
   - Consider setting `Cache-Control` headers for performance

9. **Test deployment:**
   - Open `https://csocgolf.com` in browser
   - Verify API calls work from the custom domain
   - Check browser console for CORS or auth errors

### Phase 8: Data Migration (if migrating from v1)
- Export from MongoDB
- Transform to Firestore schema
- Load via Firestore console or batch import script
- Validate record counts and sample data

### Phase 9: Testing & Validation
- Unit tests (backend and frontend)
- Integration tests (API endpoints)
- Pub/Sub end-to-end (score creation → handicap update)
- E2E tests (UI flow tests)
- Free tier quotas validation (monitor actual usage)

### Phase 10: Production Deployment
- Create staging environment (separate GCP project tier or namespace)
- Staging smoke tests
- Set up monitoring and alerts
- Gradual rollout to production
- Monitor free tier quotas

### Phase 11: Post-Launch
- Monitor Firestore read/write rates
- Monitor Cloud Run request counts and latency
- Monitor Pub/Sub message backlog
- Optimize indexes if needed
- Plan future features
