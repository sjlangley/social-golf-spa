# Handicap Calculator

Background service for calculating golf handicaps asynchronously via Google Cloud Pub/Sub. Subscribes to score events from the Golf API and updates member handicaps in Firestore using Australian Golf standards.

## Overview

The Handicap Calculator is a Pub/Sub subscriber service that:
- Listens for `score.created` events published by the Golf API
- Fetches member's last 20 scores from Firestore
- Calculates new handicap using Australian Golf standards
- Updates member's handicap record in Firestore
- Provides structured JSON logging for audit trails
- Scales independently on Google Cloud Run (free tier optimized)

**Key Benefits:**
- **Decoupled Architecture** – API remains responsive (no blocking calculations)
- **Async Processing** – Handicaps update in background
- **Fault Tolerant** – Pub/Sub retries failed messages automatically
- **Scalable** – Calculator scales independently from main API
- **Free Tier** – Pub/Sub is free up to 10 GB/month

**Technology Stack:**
- **Framework:** FastAPI (Python 3.12+)
- **Database:** Google Cloud Firestore
- **Message Queue:** Google Cloud Pub/Sub
- **HTTP Server:** Uvicorn (development) / Gunicorn (production)
- **Deployment:** Docker on Google Cloud Run

## How It Works

### Handicap Calculation Flow

```
┌─────────────────────────────┐
│   Golf API                  │
│  (Score created)            │
└──────────┬──────────────────┘
           │ publishes event
           ▼
┌──────────────────────────────┐
│  Pub/Sub Topic:              │
│  "score.created"             │
│                              │
│ {"memberId": "...", ...}     │
└──────────┬───────────────────┘
           │ push webhook
           ▼
┌──────────────────────────────┐
│  Handicap Calculator Service │
│                              │
│  1. Receive Pub/Sub message  │
│  2. Fetch last 20 scores     │
│  3. Calculate handicap       │
│  4. Update Firestore         │
│  5. Acknowledge message      │
└──────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Firestore                   │
│  handicaps/{memberId}        │
│  {handicap: 12.5, ...}       │
└──────────────────────────────┘
```

### Australian Golf Handicap Calculation

Uses best N of last 20 scores, where N depends on score count:

| Score Count | Best N | Formula |
|------------|--------|---------|
| < 6 | 1 | 1 of 5 |
| 6-8 | 2 | 2 of 8 |
| 9-11 | 3 | 3 of 11 |
| 12-14 | 4 | 4 of 14 |
| 15-16 | 5 | 5 of 16 |
| 17-18 | 6 | 6 of 18 |
| 19 | 7 | 7 of 19 |
| 20+ | 8 | 8 of 20 |

**Formula:** `handicap = (average of best N) × 0.93`

**Example:**
- Member has 12 scores
- Best 4 differentials: 10.5, 11.2, 9.8, 10.1
- Average: (10.5 + 11.2 + 9.8 + 10.1) / 4 = 10.4
- Handicap: 10.4 × 0.93 = 9.7

### Pub/Sub Message Format

When Golf API creates a score, it publishes:

```json
{
  "memberId": "member123",
  "scoreId": "score456",
  "teeId": "tee789",
  "date": "2026-02-19T10:30:00Z",
  "scratch": 85,
  "nett": 72,
  "timestamp": "2026-02-19T10:32:15Z"
}
```

The Handicap Calculator processes this and updates the member's handicap.

## Prerequisites

- **Python 3.12+**
- **Google Cloud Project** with:
  - Firestore in Native mode enabled
  - Cloud Run API enabled
  - Pub/Sub API enabled
  - Service Account with appropriate permissions
- **Service Account Key** (JSON) for local development
- **Pub/Sub Topic** named `score.created` already created

## Local Development

### 1. Set Up Python Environment

```bash
cd apps/handicap-calculator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode
pip install -e ".[dev]"
```

### 2. Configure Environment

Create `apps/handicap-calculator/.env`:

```bash
# Application settings
ENVIRONMENT=local
LOG_LEVEL=DEBUG

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Firestore (use emulator for local development)
FIRESTORE_EMULATOR_HOST=localhost:8081

# Pub/Sub subscription
PUBSUB_SUBSCRIPTION_NAME=score.created-calculator
PORT=8001
```

### 3. Start Firestore Emulator (Recommended)

```bash
# In a separate terminal
gcloud emulators firestore start --host-port=localhost:8081
```

Or use Docker:
```bash
docker run -d --name firestore-emulator -p 8081:8081 \
  oittaa/gcp-firestore-emulator:latest
```

### 4. Run the Service

```bash
# Development server with auto-reload
uvicorn handicap_calculator.app:app --reload --port 8001

# Or use gunicorn for production-like environment
gunicorn -w 1 -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8001 handicap_calculator.app:app
```

Service will be available at `http://localhost:8001`
- **Health Check:** http://localhost:8001/health

### 5. Test Manually (Without Pub/Sub)

```bash
# Trigger a calculation directly
curl -X POST http://localhost:8001/calculate \
  -H "Content-Type: application/json" \
  -d '{"memberId": "member123"}'
```

## Project Structure

```
apps/handicap-calculator/
├── src/handicap_calculator/   # Main application package
│   ├── app.py                 # FastAPI app entry point
│   ├── settings.py            # Configuration (Pydantic BaseSettings)
│   ├── enums.py               # Application enumerations
│   ├── models/                # Pydantic request/response models
│   │   ├── health.py          # Health check model
│   │   ├── score.py           # Score models
│   │   └── calculation.py     # Calculation request/response
│   ├── routes/                # API route handlers
│   │   ├── health.py          # Health check endpoint
│   │   └── calculate.py       # Manual calculation endpoint (dev only)
│   ├── services/              # Business logic
│   │   ├── firestore.py       # Firestore client wrapper
│   │   ├── pubsub.py          # Pub/Sub subscriber
│   │   └── handicap.py        # Handicap calculation logic
│   ├── middleware/            # Custom middleware
│   │   └── request_id.py      # Request tracing
│   └── utils/                 # Utilities
│       ├── logging.py         # Structured logging setup
│       └── errors.py          # Error handling
├── tests/                     # Test suite
│   ├── conftest.py            # Pytest fixtures
│   ├── test_health.py         # Health endpoint tests
│   ├── unit/                  # Unit tests
│   │   └── test_handicap.py   # Handicap calculation tests
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

### Internal Endpoints (Development/Debugging)

**Manual Handicap Calculation:**
```
POST /calculate
```
Manually trigger handicap calculation for a member (development only).

**Request:**
```json
{
  "memberId": "member123"
}
```

**Response:**
```json
{
  "memberId": "member123",
  "handicap": 12.5,
  "scoresCount": 20,
  "calculatedAt": "2026-02-19T10:30:00Z"
}
```

## Pub/Sub Integration

### Subscription Configuration

The service expects a Pub/Sub subscription configured with:
- **Topic:** `score.created` (created by Golf API)
- **Subscription:** `score.created-calculator`
- **Delivery Type:** Push webhook to HTTP endpoint
- **Push Endpoint:** `https://handicap-calculator.example.com/webhook`
- **Acknowledgement Deadline:** 600 seconds (10 minutes)

### Pub/Sub Push Webhook

When a message arrives via Pub/Sub push:

```python
@router.post("/webhook")
async def receive_pubsub_message(request: Request):
    """Receive score event from Pub/Sub push subscription."""
    body = await request.json()

    # Pub/Sub wraps message in envelope
    message = base64.b64decode(body['message']['data']).decode()
    message_data = json.loads(message)

    # Extract member ID
    member_id = message_data.get('memberId')

    # Calculate handicap
    await calculate_handicap_for_member(member_id)

    # Acknowledge by returning 200
    return {'status': 'acknowledged'}
```

### Error Handling

If calculation fails:
1. Log error with details
2. Dead-letter message to separate topic (if configured)
3. Return non-200 status code to trigger Pub/Sub retry
4. Pub/Sub automatically retries with exponential backoff

## Handicap Calculation Logic

```python
from handicap_calculator.services.handicap import calculate_handicap

# Get member's last 20 scores from Firestore
scores = await firestore.get_member_scores(member_id, limit=20)

# Calculate new handicap
handicap = calculate_handicap(scores)

# Determine best N based on score count
score_count = len(scores)
if score_count < 6:
    n = 1
elif score_count < 9:
    n = 2
# ... etc

# Get best N scores
best_scores = sorted(scores, key=lambda s: s.differential)[:n]

# Calculate average differential
average = sum(s.differential for s in best_scores) / n

# Apply 0.93 multiplier
handicap = round(average * 0.93, 1)

# Update in Firestore
await firestore.update_handicap(member_id, handicap)
```

## Testing

### Run All Tests

```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/unit               # Unit tests only
pytest tests/integration        # Integration tests only
pytest -k test_calculate        # Run specific test
pytest --cov=handicap_calculator # With coverage report
```

### Test Coverage

Coverage is enforced at 80% minimum. Configuration in `pyproject.toml`:

```ini
[tool.pytest.ini_options]
addopts = "--cov=handicap_calculator --cov-fail-under=80"
```

### Testing Handicap Calculation

```python
import pytest
from handicap_calculator.services.handicap import calculate_handicap
from handicap_calculator.models.score import Score

def test_calculate_handicap_with_six_scores():
    """Test handicap calculation with 6 scores (best 2 of 8)."""
    scores = [
        Score(differential=10.5),
        Score(differential=12.3),
        Score(differential=9.8),  # Best 1
        Score(differential=11.2),
        Score(differential=10.1),  # Best 2
        Score(differential=11.8),
    ]

    handicap = calculate_handicap(scores)

    # Best 2: 9.8, 10.1 → average 9.95 → 9.95 * 0.93 = 9.25
    assert handicap == 9.2 or handicap == 9.3  # Rounding

def test_calculate_handicap_with_twenty_scores():
    """Test handicap calculation with 20+ scores (best 8 of 20)."""
    scores = [Score(differential=i + 5.0) for i in range(20)]

    handicap = calculate_handicap(scores)

    # Best 8: 5.0-12.0 → average 8.5 → 8.5 * 0.93 = 7.905
    assert 7.8 <= handicap <= 8.0

def test_calculate_handicap_with_zero_scores():
    """Test handicap calculation with no scores."""
    handicap = calculate_handicap([])
    assert handicap == 0.0
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

**400 Bad Request**:
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Member ID is required",
    "requestId": "req_abc123"
  }
}
```

**404 Not Found**:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Member 'member123' not found",
    "requestId": "req_abc123"
  }
}
```

**500 Internal Error**:
```json
{
  "error": {
    "code": "CALCULATION_ERROR",
    "message": "Failed to calculate handicap",
    "requestId": "req_abc123"
  }
}
```

## Docker Deployment

### Build Image

```bash
cd apps/handicap-calculator
docker build -t handicap-calculator:latest .
```

### Run Container

```bash
docker run -d --name handicap-calculator \
  -p 8001:8001 \
  -e GOOGLE_CLOUD_PROJECT=my-project \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  -e PUBSUB_SUBSCRIPTION_NAME=score.created-calculator \
  handicap-calculator:latest
```

### Dockerfile Notes

- Base image: Python 3.12 slim
- Uses gunicorn + uvicorn for production
- Health check enabled
- Non-root user for security
- Single worker (Pub/Sub push typically doesn't need concurrency)

## Cloud Run Deployment

### Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR-PROJECT-ID
```

### Build & Push to Artifact Registry

```bash
# Build image
docker build -t handicap-calculator:v1 .

# Tag for Artifact Registry
docker tag handicap-calculator:v1 \
  gcr.io/YOUR-PROJECT-ID/handicap-calculator:v1

# Push to registry
docker push gcr.io/YOUR-PROJECT-ID/handicap-calculator:v1
```

### Deploy to Cloud Run

```bash
gcloud run deploy handicap-calculator \
  --image=gcr.io/YOUR-PROJECT-ID/handicap-calculator:v1 \
  --platform=managed \
  --region=us-central1 \
  --memory=512Mi \
  --timeout=300s \
  --min-instances=0 \
  --max-instances=5 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR-PROJECT-ID,PUBSUB_SUBSCRIPTION_NAME=score.created-calculator" \
  --service-account=handicap-calculator@YOUR-PROJECT-ID.iam.gserviceaccount.com
```

### Configure Pub/Sub Push Subscription

```bash
gcloud pubsub subscriptions update score.created-calculator \
  --push-endpoint=https://handicap-calculator-abc123-uc.a.run.app/webhook \
  --push-auth-service-account=handicap-calculator@YOUR-PROJECT-ID.iam.gserviceaccount.com
```

### Configure IAM Permissions

Service account needs:
- Firestore read/write access
- Pub/Sub subscriber permissions
- Secret Manager read (if using secrets)

```bash
# Grant Firestore Editor
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:handicap-calculator@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Grant Pub/Sub Subscriber
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:handicap-calculator@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"

# Grant Service Account User (for Pub/Sub push auth)
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="serviceAccount:cloud-run-pubsub@system.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" \
  --condition='resource.name=="projects/YOUR-PROJECT-ID/serviceAccounts/handicap-calculator@YOUR-PROJECT-ID.iam.gserviceaccount.com"'
```

## Monitoring & Logging

Structured JSON logs are automatically sent to Cloud Logging:

```json
{
  "timestamp": "2026-02-19T10:30:00.000Z",
  "severity": "INFO",
  "requestId": "req_abc123",
  "memberId": "member123",
  "handicap": 12.5,
  "scoresCount": 20,
  "duration_ms": 245,
  "status": "success"
}
```

View logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=handicap-calculator" \
  --limit 50 \
  --format json
```

### Key Metrics

- **Message processing time** – How long handicap calculations take
- **Pub/Sub acknowledgement rate** – Failed vs successful calculations
- **Dead-letter messages** – Messages that failed after retries
- **Firestore write latency** – Time to update handicap records

## Contributing

1. Create feature branch: `git checkout -b feature/description`
2. Make changes and write tests
3. Run linting: `ruff check src/ && ruff format src/`
4. Run tests: `pytest --cov=golf_api`
5. Commit: `git commit -m "feat: description"`
6. Push: `git push origin feature/description`
7. Create Pull Request

See [Security Documentation](/docs/security.md) for security guidelines.

## Troubleshooting

### "Module not found: handicap_calculator"
- Install in editable mode: `pip install -e ".[dev]"`
- Check PYTHONPATH: `sys.path`

### "FIRESTORE_EMULATOR_HOST not set"
- Emulator not running, start it: `gcloud emulators firestore start`
- Or configure in `.env`: `FIRESTORE_EMULATOR_HOST=localhost:8081`

### "Pub/Sub subscription not found"
- Create subscription: `gcloud pubsub subscriptions create score.created-calculator --topic=score.created`
- Configure push endpoint in Cloud Run service

### "Member not found" errors
- Golf API may not have created the member yet
- Check Firestore `members` collection has the member ID
- Verify Firestore permissions for service account

### "Calculation timeout"
- Pub/Sub acknowledgement deadline too short (should be ≥600 seconds)
- Firestore emulator may be slow; increase in `pyproject.toml`
- Consider increasing Cloud Run timeout to 300+ seconds

### Pub/Sub messages not arriving
- Check subscription exists: `gcloud pubsub subscriptions list`
- Verify push endpoint configured: `gcloud pubsub subscriptions describe score.created-calculator`
- Check service account permissions for Pub/Sub
- Verify Cloud Run service can be reached from Pub/Sub

## License

Apache 2.0

## Support

For issues, questions, or contributions, contact the development team or open an issue in the repository.
