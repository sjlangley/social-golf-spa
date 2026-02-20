# Golf API

FastAPI backend for the Caringbah Social Golf Club management system. Handles member management, score recording, match results, and handicap calculation via Google Cloud Platform.

## Overview

The Golf API is a stateless REST service that:
- Verifies Google OAuth 2.0 ID tokens on every request
- Enforces role-based authorization (admin/member)
- Records scores and publishes events to Pub/Sub for async handicap calculation
- Stores all data in Google Cloud Firestore
- Provides structured JSON logging for Cloud Logging integration
- Scales to zero on Google Cloud Run (free tier optimized)

**Technology Stack:**
- **Framework:** FastAPI (Python 3.12+)
- **Authentication:** Firebase Admin SDK (Google ID tokens)
- **Database:** Google Cloud Firestore
- **Message Queue:** Google Cloud Pub/Sub
- **HTTP Server:** Uvicorn (development) / Gunicorn (production)
- **Deployment:** Docker on Google Cloud Run

## Prerequisites

- **Python 3.12+**
- **Google Cloud Project** with:
  - Firestore in Native mode enabled
  - Cloud Run API enabled
  - Pub/Sub API enabled
  - Service Account with appropriate permissions
- **Service Account Key** (JSON) for local development
- **Google OAuth 2.0 credentials** configured

## Local Development

### 1. Set Up Python Environment

```bash
cd apps/golf-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode
pip install -e ".[dev]"
```

### 2. Configure Environment

Create `apps/golf-api/.env`:

```bash
# Application settings
ENVIRONMENT=local
LOG_LEVEL=DEBUG
AUTH_DISABLED=false

# CORS (allow frontend in development)
CLIENT_ORIGINS=http://localhost:5173,http://localhost:3000

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Firestore (use emulator for local development)
FIRESTORE_EMULATOR_HOST=localhost:8081

# Pub/Sub (optional, for async handicap calculation)
PUBSUB_TOPIC_NAME=score.created
```

### 3. Start Firestore Emulator (Recommended)

```bash
# In a separate terminal
gcloud emulators firestore start --host-port=localhost:8081
```

Or use the Firestore emulator Docker image:
```bash
docker run -d --name firestore-emulator -p 8081:8081 \
  oittaa/gcp-firestore-emulator:latest
```

### 4. Run the Server

```bash
# Development server with auto-reload
uvicorn golf_api.app:app --reload --port 8000

# Or use gunicorn for production-like environment
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 golf_api.app:app
```

API will be available at `http://localhost:8000`
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Project Structure

```
apps/golf-api/
├── src/golf_api/              # Main application package
│   ├── app.py                 # FastAPI app entry point
│   ├── settings.py            # Configuration (Pydantic BaseSettings)
│   ├── enums.py               # Application enumerations
│   ├── models/                # Pydantic request/response models
│   │   ├── health.py          # Health check model
│   │   ├── member.py          # Member models
│   │   ├── score.py           # Score models
│   │   └── match.py           # Match models
│   ├── routes/                # API route handlers
│   │   ├── health.py          # Health check endpoint
│   │   ├── members.py         # Member endpoints
│   │   ├── scores.py          # Score endpoints
│   │   └── matches.py         # Match endpoints
│   ├── services/              # Business logic
│   │   ├── firestore.py       # Firestore client wrapper
│   │   ├── pubsub.py          # Pub/Sub publisher
│   │   ├── auth.py            # Authentication/authorization
│   │   └── handicap.py        # Handicap calculation helper
│   ├── middleware/            # Custom middleware
│   │   ├── auth.py            # Token verification
│   │   └── request_id.py      # Request tracing
│   └── utils/                 # Utilities
│       ├── logging.py         # Structured logging setup
│       └── errors.py          # Error handling
├── tests/                     # Test suite
│   ├── conftest.py            # Pytest fixtures
│   ├── test_health.py         # Health endpoint tests
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── Dockerfile                 # Docker image definition
├── pyproject.toml             # Project configuration & dependencies
├── ruff.toml                  # Linting/formatting config (root)
└── README.md                  # This file
```

## API Endpoints

### Public Endpoints

**Health Check:**
```
GET /health
```
Returns `{"status": "OK"}` (200)

### Authentication Required

All endpoints below require valid Google ID token in `Authorization` header:
```http
Authorization: Bearer <ID_TOKEN>
```

**Members:**
```
GET    /api/v1/members              # List members (paginated)
POST   /api/v1/members              # Create member (admin only)
GET    /api/v1/members/{id}         # Get member details
PUT    /api/v1/members/{id}         # Update member (admin only)
DELETE /api/v1/members/{id}         # Delete member (admin only)
```

**Scores:**
```
GET    /api/v1/scores               # List scores (paginated)
POST   /api/v1/scores               # Create score (admin only) → publishes to Pub/Sub
GET    /api/v1/scores/{id}          # Get score details
PUT    /api/v1/scores/{id}          # Update score (admin only)
DELETE /api/v1/scores/{id}          # Delete score (admin only)
```

**Matches:**
```
GET    /api/v1/matches              # List matches (paginated)
POST   /api/v1/matches              # Create match (admin only)
GET    /api/v1/matches/{id}         # Get match details
PUT    /api/v1/matches/{id}         # Update match (admin only)
DELETE /api/v1/matches/{id}         # Delete match (admin only)
```

**Handicaps:**
```
GET    /api/v1/handicaps            # List handicap records (paginated)
GET    /api/v1/handicaps/{memberId} # Get member's handicap history
```

See API documentation at `/docs` for full request/response schemas.

## Authentication & Authorization

### Token Verification

Every protected request must include a valid Google ID token:

```typescript
// Frontend example
const token = await googleIdentitiesSDK.getIdToken();
const response = await fetch('https://api.example.com/api/v1/members', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

Backend verifies token using Firebase Admin SDK:
- Validates signature using Google's public keys
- Checks token expiration
- Verifies audience (Google Client ID)
- Verifies issuer (accounts.google.com)

### Role-Based Access Control

**Two roles exist:**
- `admin` – Can create/update/delete resources, record scores/matches
- `member` – Read-only access to public data

**Assignment:**
- First user to log in: automatically `admin`
- Subsequent users: default `member` role
- Admins can promote other users to `admin`

**Example:** Only admins can record scores
```python
@router.post("/api/v1/scores")
async def create_score(
    score: ScoreCreate,
    user = Depends(require_admin),
):
    # User is guaranteed to have admin role
    ...
```

See [Security Documentation](/docs/security.md) for detailed auth flow.

## Testing

### Run All Tests

```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/unit               # Unit tests only
pytest tests/integration        # Integration tests only
pytest -k test_health           # Run specific test
pytest --cov=golf_api           # With coverage report
```

### Test Coverage

Coverage is enforced at 80% minimum. Configuration in `pyproject.toml`:

```ini
[tool.pytest.ini_options]
addopts = "--cov=golf_api --cov-report=term-missing --cov-fail-under=80"
```

To view HTML coverage report:
```bash
pytest --cov=golf_api --cov-report=html
open htmlcov/index.html
```

### Writing Tests

Use the `async_test_client` fixture (defined in `conftest.py`):

```python
@pytest.mark.asyncio
async def test_members_endpoint(async_test_client):
    """Test listing members."""
    response = await async_test_client.get('/api/v1/members')
    assert response.status_code == 200
    assert 'data' in response.json()
```

Mock Firebase authentication in tests:
```python
@pytest.mark.asyncio
async def test_admin_can_create_score(async_test_client, mocker):
    """Test that admins can create scores."""
    # Mock token verification
    mocker.patch('golf_api.middleware.auth.verify_id_token',
                 return_value={'sub': 'user123', 'email': 'admin@example.com'})

    # Mock role lookup
    mocker.patch('golf_api.services.auth.get_user_role',
                 return_value='admin')

    response = await async_test_client.post('/api/v1/scores',
                                             json={...})
    assert response.status_code == 201
```

## Code Quality

### Linting & Formatting

```bash
# Check code style (from root directory)
ruff check apps/golf-api/src/

# Format code
ruff format apps/golf-api/src/

# Type checking
pyrefly check src/
```

Configuration in `ruff.toml` (root):
- Line length: 80 characters
- Quote style: single quotes
- Import sorting: PEP 8 compliant

### Pre-Commit

Config lint/format before committing:
```bash
# From apps/golf-api
ruff check src/ && ruff format src/ && pyrefly check src/
```

## Error Handling

API returns consistent error responses:

**400 Bad Request** (validation error):
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "First name is required",
    "details": {"field": "firstName"},
    "requestId": "req_abc123"
  }
}
```

**401 Unauthorized** (invalid/expired token):
```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Invalid or expired token",
    "requestId": "req_abc123"
  }
}
```

**403 Forbidden** (insufficient permissions):
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Admin access required",
    "requestId": "req_abc123"
  }
}
```

**404 Not Found**:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Member with ID 'xyz' not found",
    "requestId": "req_abc123"
  }
}
```

See error handling in `golf_api/utils/errors.py`.

## Pub/Sub Integration

When a score is created, an event is published to Pub/Sub for async handicap calculation:

```python
# In routes/scores.py
@router.post("/api/v1/scores", status_code=201, response_model=Score)
async def create_score(
    score: ScoreCreate,
    user = Depends(require_admin),
):
    # 1. Save score to Firestore
    created_score = await db.create_score(score)

    # 2. Publish event to Pub/Sub topic "score.created"
    await pubsub.publish('score.created', {
        'memberId': score.member_id,
        'scoreId': created_score.id,
        'timestamp': datetime.utcnow().isoformat(),
    })

    # 3. Return immediately (handicap calculates in background)
    return {'data': created_score, 'handicap_status': 'calculating'}
```

The Handicap Calculator service subscribes to this topic and updates member handicaps asynchronously.

## Docker Deployment

### Build Image

```bash
cd apps/golf-api
docker build -t golf-api:latest .
```

### Run Container

```bash
docker run -d --name golf-api \
  -p 8000:8000 \
  -e GOOGLE_CLOUD_PROJECT=my-project \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  -e CLIENT_ORIGINS=https://csocgolf.com \
  golf-api:latest
```

### Dockerfile Notes

- Base image: Python 3.12 slim
- Uses gunicorn + uvicorn for production
- Health check enabled
- Non-root user for security

## Cloud Run Deployment

### Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR-PROJECT-ID
```

### Build & Push to Artifact Registry

```bash
# Build image
docker build -t golf-api:v1 .

# Tag for Artifact Registry
docker tag golf-api:v1 \
  gcr.io/YOUR-PROJECT-ID/golf-api:v1

# Push to registry
docker push gcr.io/YOUR-PROJECT-ID/golf-api:v1
```

### Deploy to Cloud Run

```bash
gcloud run deploy golf-api \
  --image=gcr.io/YOUR-PROJECT-ID/golf-api:v1 \
  --platform=managed \
  --region=us-central1 \
  --memory=512Mi \
  --timeout=300s \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR-PROJECT-ID,CLIENT_ORIGINS=https://csocgolf.com" \
  --service-account=golf-api@YOUR-PROJECT-ID.iam.gserviceaccount.com
```

### Configure Secret Manager Access

Service account needs permissions:
```bash
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:golf-api@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Monitoring & Logging

Structured JSON logs are automatically sent to Cloud Logging:

```json
{
  "timestamp": "2026-02-19T10:30:00.000Z",
  "severity": "INFO",
  "requestId": "req_abc123",
  "user": "user@example.com",
  "method": "POST",
  "path": "/api/v1/scores",
  "duration_ms": 45,
  "status": 201
}
```

View logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=golf-api" \
  --limit 50 \
  --format json
```

## Contributing

### Before Committing (REQUIRED)

**⚠️ All checks must pass before committing. CI will fail if you skip these steps.**

Run these commands in order from `apps/golf-api/`:

```bash
# 1. Format code
ruff format .

# 2. Check linting
ruff check .

# 3. Type check
pyright .

# 4. Run tests with coverage (minimum 80% required)
pytest --cov=src/golf_api --cov-fail-under=80 --cov-report=term-missing
```

**All checks must pass before you can commit.**

### Contribution Workflow

1. Create feature branch: `git checkout -b feature/description`
2. Make changes and write tests
3. **Run all pre-commit checks above** ⬆️
4. Commit using conventional syntax: `git commit -m "feat: description"`
5. Push: `git push origin feature/description`
6. Create Pull Request

See [Security Documentation](/docs/security.md) for security guidelines.

## Troubleshooting

### "Module not found: golf_api"
- Install in editable mode: `pip install -e ".[dev]"`
- Check Python path: `sys.path`

### "FIRESTORE_EMULATOR_HOST not set"
- Emulator not running, start it: `gcloud emulators firestore start`
- Or configure in `.env`: `FIRESTORE_EMULATOR_HOST=localhost:8081`

### "Invalid Google Client ID"
- Check `GOOGLE_APPLICATION_CREDENTIALS` points to valid service account JSON
- Verify service account has Firestore permissions

### "CORS error in browser"
- Check `CLIENT_ORIGINS` includes frontend domain
- Frontend must send `Authorization` header with bearer token

### Tests timeout
- Firestore emulator may be slow; increase pytest timeout in `pyproject.toml`
- Or use `fake-firestore` for unit tests

## License

MIT

## Support

For issues, questions, or contributions, contact the development team or open an issue in the repository.
