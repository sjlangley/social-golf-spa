# Security Documentation

This document outlines the security architecture, best practices, and guidelines for the Caringbah Social Golf Club management system.

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication](#authentication)
3. [Authorization](#authorization)
4. [Transport Security](#transport-security)
5. [Data Protection](#data-protection)
6. [Secret Management](#secret-management)
7. [Input Validation & Prevention](#input-validation--prevention)
8. [Code Security](#code-security)
9. [Dependency Management](#dependency-management)
10. [Security Checklist](#security-checklist)
11. [Incident Response](#incident-response)

## Security Overview

### Architecture Principles

The security posture is built on these key principles:

- **Defense in Depth** – Multiple layers of security controls
- **Least Privilege** – Services and users have minimal required permissions
- **Zero Trust** – All requests are verified, even internal ones
- **Fail Secure** – Errors default to denying access
- **Encryption in Transit** – All communication is HTTPS only
- **Never Trust the Client** – Server always verifies authorization

### Core Components

```
┌─────────────────────────────────────────┐
│      React SPA (Cloud Storage)          │
│  • HTTPS enforced                        │
│  • Google Sign-In integration            │
│  • No sensitive data stored              │
└──────────────┬────────────────────────────┘
               │
               │ HTTPS only
               │ Bearer <ID_TOKEN> header
               │
               ▼
┌─────────────────────────────────────────┐
│      FastAPI Backend (Cloud Run)         │
│  • Token verification on every request   │
│  • Role-based authorization              │
│  • Input validation (Pydantic)           │
│  • Structured logging                    │
│  • CORS restricted                       │
└──────────────┬────────────────────────────┘
               │
               ├── Firestore (encrypted)
               ├── Secret Manager (encrypted)
               ├── Cloud Logging (audited)
               └── Pub/Sub (IAM controlled)
```

## Authentication

### OAuth 2.0 with Google Identity Services

The system uses Google OAuth 2.0 for user authentication. The frontend obtains an ID token which is verified server-side.

#### Frontend: Obtaining ID Token

```typescript
// User clicks "Sign in with Google"
// Google Identity Services (google accounts.google.com) handles the OAuth flow
const credential = response.credential; // JWT (ID Token)

// Token is kept in memory (React state), never in localStorage
// Token is included in Authorization header for all API calls
fetch('https://api.csocgolf.com/api/v1/members', {
  headers: {
    'Authorization': `Bearer ${credential}`
  }
});
```

**Token Properties:**
- **Issuer:** `https://accounts.google.com`
- **Lifetime:** 1 hour (short-lived)
- **Signed:** RS256 algorithm with Google's private key
- **Refreshable:** Frontend can request new token silently if needed

#### Backend: Token Verification

```python
from firebase_admin import auth
from fastapi import Depends, HTTPException, Header, status

async def get_current_user(authorization: str = Header(None)):
    """Extract and verify ID token from Authorization header."""

    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.split('Bearer ')[1]

    try:
        # Firebase Admin SDK verifies:
        # ✓ Signature (using Google's public keys from JWKS endpoint)
        # ✓ Expiration (exp claim must be in future)
        # ✓ Audience (must match our Google Client ID)
        # ✓ Issuer (must be accounts.google.com)
        # ✓ Not on revocation list (if user signed out)

        decoded_token = auth.verify_id_token(token)

        user_id = decoded_token['sub']      # Google UID (immutable)
        email = decoded_token['email']       # User's email
        email_verified = decoded_token['email_verified']

        return {
            'id': user_id,
            'email': email,
            'email_verified': email_verified
        }

    except auth.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature"
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
```

**Key Security Points:**

✓ **Signature Verification:** Firebase Admin SDK uses Google's public keys to verify the signature. This prevents token forgery.

✓ **Expiration Check:** Expired tokens are rejected. Frontend must request a new token if the old one expires.

✓ **Audience Validation:** The token's `aud` claim must match our Google Client ID. This prevents tokens meant for other apps from being used here.

✓ **Issuer Validation:** Only tokens from `accounts.google.com` are accepted.

✓ **Public Key Caching:** Firebase Admin SDK caches Google's public keys for performance, automatically refreshing when keys rotate.

### Session Management

**No Sessions:** The system is stateless. Each request includes its own authorization credentials (ID token).

**Why Stateless?**
- Simpler architecture (no session storage needed)
- Better for horizontal scaling (no session affinity required)
- Complements Cloud Run's auto-scaling
- More secure (no session hijacking risk)

### Token Storage (Frontend)

**Location:** React component state (memory only)

**NOT in localStorage:** Tokens are not persisted to local storage because:
- localStorage is accessible via XSS attacks
- Tokens should live only for as long as the browser session
- New token obtained on page refresh (Google caches user login)

**NOT in Cookies:** Tokens are not stored in cookies because:
- Would require HTTPOnly flag (can't access in JavaScript)
- Would require SameSite attribute (more complexity)
- Authorization header is simpler and just as secure

### Token Expiration & Refresh

When token expires:
1. Frontend detects 401 response from API
2. Frontend re-authenticates with Google using `useGoogleLogin` hook
3. New token is obtained
4. Original request is retried

```typescript
// Example: Automatic retry on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const newToken = await getNewToken(); // Re-auth with Google
      error.config.headers.Authorization = `Bearer ${newToken}`;
      return apiClient(error.config);
    }
    return Promise.reject(error);
  }
);
```

## Authorization

### Role-Based Access Control (RBAC)

Two roles exist:

| Role | Permissions | Assignment |
|------|-------------|-----------|
| `admin` | Create/update/delete members, scores, matches | First user auto-promoted, admins can delegate |
| `member` | Read-only access to public data | Default for new users |

### User Role Lookup

After verifying the token, role is fetched from Firestore:

```python
# 1. Token is verified (get user_id from decoded token)
decoded_token = auth.verify_id_token(token)
user_id = decoded_token['sub']

# 2. Look up user in Firestore to get role
user_doc = firestore_client.collection('users').document(user_id).get()

if not user_doc.exists:
    # First login - create user doc with admin role
    role = await create_first_user(user_id, email)
else:
    role = user_doc.get('role', 'member')

return {'id': user_id, 'email': email, 'role': role}
```

**Why fetch role from database?**
- Role can be revoked without needing new token
- Role changes take effect immediately
- Role is not trusted from ID token (ID token doesn't claim role)
- Single source of truth (Firestore)

### Endpoint Protection

**Public Endpoints** (no auth required):
```python
@router.get("/health")
async def health_check():
    """Public health check for monitoring."""
    return {"status": "ok"}

@router.get("/api/v1/members")
async def list_members(
    page: int = 1,
    page_size: int = 20,
):
    """List members (public read)."""
    # Optional: could require authentication for privacy
    return members
```

**Member-Only Endpoints** (any authenticated user):
```python
@router.get("/api/v1/members/{member_id}")
async def get_member(
    member_id: str,
    user = Depends(get_current_user),
):
    """Get member details (authenticated users only)."""
    return member
```

**Admin-Only Endpoints** (admin role required):
```python
@router.post("/api/v1/members")
async def create_member(
    member: MemberCreate,
    user = Depends(require_admin),
):
    """Create a new member (admin only)."""
    return created_member

@router.delete("/api/v1/members/{member_id}")
async def delete_member(
    member_id: str,
    user = Depends(require_admin),
):
    """Delete a member (admin only)."""
    return {"deleted": True}
```

### Enforcing Authorization

**Never trust the client:** Always verify on backend.

```python
# ❌ WRONG: Trusting client role
if (user.role === 'admin') {
  <AdminButton />  // UI hidden, but user can still call delete API!
}

# ✅ CORRECT: Verifying on backend
@router.delete("/api/v1/members/{member_id}")
async def delete_member(
    member_id: str,
    user = Depends(require_admin),  # ← Forces role check
):
    # This endpoint is unreachable without admin role
    ...
```

### Cross-Tenant Access

**Single Tenant:** The system is not multi-tenant. All members and matches belong to one club.

If multi-tenancy is added, all endpoints must filter by club:
```python
@router.get("/api/v1/members")
async def list_members(
    user = Depends(get_current_user),
    db = Depends(get_firestore),
):
    # MUST filter by user's club
    members = db.collection('members')\
        .where('clubId', '==', user.clubId)\
        .stream()
    return members
```

## Transport Security

### HTTPS Enforcement

**All traffic must be HTTPS.** HTTP is not permitted.

**Frontend (Cloud Storage):**
- Google-managed SSL certificate
- Automatically renewed
- HTTP automatically redirects to HTTPS
- No configuration required

**Backend (Cloud Run):**
- Google-managed SSL certificate
- No configuration required
- All traffic encrypted with TLS 1.2+

**Configuration:**
```python
# Ensure backend redirects HTTP to HTTPS
# Cloud Run defaults require HTTPS
# If behind load balancer, ensure X-Forwarded-Proto: https
```

### CORS (Cross-Origin Resource Sharing)

Backend restricts API access to authorized domains only:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://csocgolf.com",           # Production frontend
        "https://staging.csocgolf.com",   # Staging frontend
        # Note: localhost restricted to development only
    ],
    allow_credentials=False,  # No cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,  # Browser caches preflight for 1 hour
)
```

**Why CORS Matters:**
- Prevents JavaScript from other domains calling our API
- Frontend specifies which origins are allowed
- Preflight requests check permissions before sending actual request
- Credentials (cookies) can't be sent with requests (`allow_credentials=False`)

**Frontend CORS Policy** (Cloud Storage):
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

### Certificate Pinning

**Not currently implemented.** For native mobile apps, consider certificate pinning to prevent MITM attacks:
- Pin Google's root CA certificate
- Pin certificate public key hash
- Detect and alert on certificate changes

## Data Protection

### Data at Rest

**Firestore Encryption:**
- All data encrypted at rest with Google-managed keys
- No customer-managed encryption keys (free tier limitation)
- Encryption transparent to application

**Secret Manager Encryption:**
- All secrets encrypted at rest with Google-managed keys
- Only accessible via authenticated service account
- Audit logs track all access

### Data in Transit

**HTTPS/TLS:**
- All traffic encrypted with TLS 1.2+
- Perfect Forward Secrecy (ephemeral keys)
- No unencrypted protocols used

**Pub/Sub Messages:**
- Published to Pub/Sub (internal GCP network)
- Encrypted in transit
- Short-lived (message retention ~7 days)

### Data Retention & Deletion

**No automatic deletion:** Historical data (scores, matches, handicaps) is retained indefinitely.

**User Deletion:** When a user account is deleted:
1. User document removed from Firestore
2. Access revoked immediately
3. Historical scores/matches retained (for club records)
4. Optional: Anonymize user data

```python
async def delete_user(user_id: str, current_user = Depends(require_admin)):
    """Delete user account and revoke access."""

    # Remove from users collection
    firestore_client.collection('users').document(user_id).delete()

    # Optional: Anonymize scores/matches
    # Leave historical records but remove user association

    logger.info(f"User {user_id} deleted by {current_user.id}")
```

### Personal Data Handling

**Collected Data:**
- Email (from Google)
- Name (from Google profile)
- Profile picture URL (from Google)
- Golf scores and handicaps
- Contact phone numbers (club members only)

**Data Minimization:**
- Only collect what's necessary for golf club operations
- Don't track additional data
- Don't integrate analytics (Google Analytics not needed)

**Data Access:**
- All access logs in Cloud Logging
- Admin actions include user ID
- Pub/Sub messages include request ID for tracing

## Secret Management

### Secrets in Use

| Secret | Use | Storage | Rotation |
|--------|-----|---------|----------|
| Google Client ID | OAuth configuration | Environment variable | Never (public) |
| Google Client Secret | Backend OAuth | Secret Manager | Quarterly |
| Service Account Key | Backend authentication | Secret Manager | Never (use shorter-lived workload identity instead) |
| Firebase Config | Firestore auth | Environment variable | Never (public) |
| Pub/Sub Topic Name | Score event publishing | Environment variable | Never |

### Storing Secrets

**Production (Cloud Run):**
Use Google Cloud Secret Manager:

```python
from google.cloud import secretmanager

def get_secret(secret_id: str, version_id: str = "latest"):
    """Fetch secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')

    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})

    return response.payload.data.decode("UTF-8")

# Usage
db_password = get_secret('database-password')
```

**Local Development:**
Use `.env` file (never committed):

```bash
# apps/golf-api/.env (git-ignored)
GOOGLE_CLOUD_PROJECT=my-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
API_SECRET_KEY=dev-secret-key-only
FIRESTORE_EMULATOR_HOST=localhost:8080
```

**Environment Variables (Safe to Commit):**
```bash
# Config file: apps/golf-api/.env.example (git-tracked)
GOOGLE_CLOUD_PROJECT=my-project
LOG_LEVEL=INFO
PUBSUB_TOPIC_NAME=score.created
CORS_ORIGINS=https://csocgolf.com
```

### Secret Rotation

**Google Client Secret:**
- Manually rotate quarterly
- Create new credential in Google Consent Screen
- Update in Secret Manager
- Gradual rollout (keep old and new valid for 24 hours)

**Service Account Keys:**
- Use Workload Identity instead of long-lived keys
- If keys needed: rotate annually

**No Rotation Needed:**
- Google Client ID (public)
- Pub/Sub topic names (internal routing, not sensitive)

### Audit Trail

All secret accesses logged to Cloud Audit Logs:
```
service: secretmanager.googleapis.com
protoPayload:
  methodName: google.cloud.secretmanager.v1.SecretManagerService.AccessSecretVersion
  principalEmail: backend-service-account@project.iam.gserviceaccount.com
  resourceName: projects/my-project/secrets/database-password/versions/latest
  timestamp: 2026-02-19T10:30:00.000Z
```

## Input Validation & Prevention

### SQL Injection

**Not Applicable:** Firestore is NoSQL. No SQL injection possible.

However, must validate:
- Firestore document IDs are valid format
- No unexpected operators in query strings

```python
# ❌ UNSAFE: Unvalidated user input in query
def get_member(member_id: str):
    doc = firestore_client.collection('members').document(member_id).get()
    # If member_id contains special chars, could cause issues

# ✅ SAFE: Validate document ID
def get_member(member_id: str = Query(..., regex="^[a-zA-Z0-9_-]{20,}$")):
    doc = firestore_client.collection('members').document(member_id).get()
```

### XSS (Cross-Site Scripting)

**Frontend:**
React automatically escapes all text by default:

```typescript
// ✓ Safe: React escapes HTML
<div>{user.name}</div>  // <script> tags are escaped

// ✗ Unsafe: Only use dangerouslySetInnerHTML with trusted content
<div dangerouslySetInnerHTML={{ __html: user.bio }} />
```

**Backend:**
Always return JSON, never HTML. If HTML rendering needed, use template escaping:

```python
from jinja2 import Markup, escape

# ✓ Safe: Variables escaped by default
template = jinja_env.from_string('Hello {{ username }}')
return template.render(username=user_input)

# ✗ Unsafe: Markup switches off escaping
template = jinja_env.from_string('Hello {{ username|safe }}')
return template.render(username=user_input)  # Dangerous!
```

### CSRF (Cross-Site Request Forgery)

**Not Applicable:** No cookies used for authentication. All requests use Bearer token in Authorization header, which cannot be sent by cross-origin requests.

If cookies were used, would need CSRF tokens:
```python
# Example (NOT CURRENT IMPLEMENTATION):
# Would need CSRF token verification middleware
@router.post("/api/v1/members")
async def create_member(
    member: MemberCreate,
    csrf_token: str = Form(...),
):
    # Verify CSRF token matches session
```

### Input Validation

All inputs validated with Pydantic:

```python
from pydantic import BaseModel, Field, EmailStr

class MemberCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(...)
    phone: Optional[List[str]] = Field(default_factory=list)
    member_no: int = Field(..., gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "member_no": 123
            }
        }

# Validation happens automatically
member = MemberCreate(**request_data)  # Raises ValidationError if invalid

@router.post("/api/v1/members", response_model=Member)
async def create_member(member: MemberCreate):
    # member is guaranteed to be valid
    return await db.create_member(member)
```

### Rate Limiting

**Not Currently Implemented.** Future enhancement:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/api/v1/members")
@limiter.limit("100/minute")
async def list_members():
    # User limited to 100 requests per minute
    return members
```

### Request Size Limits

Cloud Run has default limits:
- Max request size: 32 MB
- Max request timeout: 60 seconds (can increase to 300 for long polls)

Custom limits:
```python
from fastapi import Request, HTTPException

@app.middleware("http")
async def size_limit_middleware(request: Request, call_next):
    if request.method == "POST" or request.method == "PUT":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1_000_000:  # 1 MB
            raise HTTPException(status_code=413, detail="Payload too large")

    return await call_next(request)
```

## Code Security

### Secure Coding Practices

**Dependency Pinning:**
- Pin package versions to prevent unexpected updates
- Use lock files (requirements.lock, package-lock.json)
- Review dependency updates before merging

**Secret Handling:**
- Never log secrets (check before committing)
- Never print token values to console
- Use dummy values in error messages

```python
# ✓ Safe: No token in logs
logger.error(f"Failed to verify token for user {user_id}")

# ✗ Unsafe: Token exposed in logs
logger.error(f"Failed to verify token: {token}")
```

**Error Messages:**
- Don't expose system details to attackers
- Log details server-side, send generic message to client

```python
# ✓ Safe: Generic error to client
raise HTTPException(
    status_code=500,
    detail="An error occurred processing your request"
)
# Server logs: {"error": "PermissionError: /etc/shadow", "user": "123"}

# ✗ Unsafe: Detailed error to client
raise HTTPException(
    status_code=500,
    detail=f"Permission denied: {exc}"
)  # Attacker learns system details
```

**Async/Await:**
Always use `await` to prevent race conditions:

```python
# ✓ Safe: Sequential operations
member = await db.get_member(member_id)
member.scores = await db.get_scores(member_id)
member.handicap = await calculate_handicap(member.scores)

# ✗ Potentially unsafe: Concurrent operations without proper handling
# Could violate business logic if operations interact
member = await asyncio.gather(
    db.get_member(member_id),
    db.get_scores(member_id),
)
```

### Security Testing

**Unit Tests:**
```python
def test_unauthorized_delete_fails():
    """Non-admin users cannot delete members."""
    with pytest.raises(HTTPException, match="permission denied"):
        delete_member(
            member_id="123",
            current_user={"id": "user", "role": "member"}
        )

def test_admin_can_delete():
    """Admin users can delete members."""
    response = delete_member(
        member_id="123",
        current_user={"id": "admin", "role": "admin"}
    )
    assert response.deleted is True
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_invalid_token_denied():
    """Invalid tokens are rejected."""
    response = client.get(
        "/api/v1/members",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_expired_token_denied():
    """Expired tokens are rejected."""
    expired_token = create_expired_token()
    response = client.get(
        "/api/v1/members",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
```

## Dependency Management

### Frontend Dependencies

Key security packages:
- **firebase** – OAuth and ID token handling
- **@tanstack/react-query** – API data fetching
- **axios** – HTTP client (use for auth headers)
- **zod** – Runtime type validation (additional to TypeScript)

Vulnerabilities:
- Run `npm audit` regularly
- Keep dependencies updated
- Review security advisories

### Backend Dependencies

Key security packages:
- **fastapi** – Web framework (actively maintained)
- **firebase-admin** – Token verification (critical for auth)
- **pydantic** – Input validation (prevents injection attacks)
- **google-cloud-firestore** – Database client
- **google-cloud-secret-manager** – Secret access

Vulnerabilities:
- Run `pip audit` regularly
- Keep dependencies updated
- Run security scanners: `bandit`, `safety`

### Dependency Updates

**Process:**
1. Auto-update patches (minor version updates)
2. Manual review of minor updates
3. Manual review and testing of major updates
4. Check security advisories on all updates

**Automated:**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/apps/golf-ui"
    schedule:
      interval: "weekly"
    allow:
      - dependency-type: "production"

  - package-ecosystem: "pip"
    directory: "/apps/golf-api"
    schedule:
      interval: "weekly"
    allow:
      - dependency-type: "production"
```

## Security Checklist

Use this checklist before deploying code changes:

### Code Review

- [ ] No hardcoded secrets or API keys
- [ ] All user inputs validated with Pydantic
- [ ] All protected endpoints check `Depends(require_admin)` or `Depends(get_current_user)`
- [ ] No tokens in logs or error messages
- [ ] CORS middleware configured correctly
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities

### Authentication & Authorization

- [ ] Token verification uses Firebase Admin SDK
- [ ] Role fetched from Firestore (not trusted from token)
- [ ] Admin actions require `require_admin` dependency
- [ ] Unauthorized actions return 403 (not 404)
- [ ] Token expiration handled gracefully

### Data Protection

- [ ] Sensitive data not logged
- [ ] Error messages don't expose system details
- [ ] Firestore rules restrict data access
- [ ] No unnecessary data collection
- [ ] User data exportable/deletable

### Deployment

- [ ] Environment variables set in Secret Manager
- [ ] Service account has minimal permissions
- [ ] HTTPS enforced
- [ ] CORS headers correct
- [ ] Rate limiting enabled (if needed)
- [ ] Monitoring and alerting configured
- [ ] Backup procedure documented

### Dependencies

- [ ] `npm audit` passes (no critical vulnerabilities)
- [ ] `pip audit` passes (no critical vulnerabilities)
- [ ] All dependencies have known licenses
- [ ] Pinned versions in package files
- [ ] Lock files committed

## Incident Response

### Potential Security Incidents

**Unauthorized Access**

If someone gains unauthorized access:
1. Immediately revoke their role in Firestore
2. Review their actions in Cloud Audit Logs
3. Alert affected users if data was exposed
4. Analyze how they gained access
5. Prevent recurrence (e.g., fix authorization check)

```python
# Revoke admin access
firestore_client.collection('users').document('compromised_user').update({
    'role': 'member'  # Demote to member
})
```

**Leaked Secret**

If an API key or token is leaked:
1. Immediately rotate the secret in Secret Manager
2. Invalidate old token
3. Review audit logs for unauthorized access
4. Check for data exfiltration
5. Re-deploy services with new secret

```bash
# Create new secret version
gcloud secrets versions add DATABASE_PASSWORD --data-file=- < new_password.txt

# Mark old version as destroyed
gcloud secrets versions destroy 1
```

**Data Breach**

If data is compromised:
1. Investigate scope (what data, who affected?)
2. Notify affected members
3. Document findings
4. Update security policies to prevent recurrence
5. Consider regulatory notifications (privacy frameworks)

**DDoS Attack**

If under attack:
1. Enable Cloud Armor (GCP DDoS protection)
2. Rate limiting on API endpoints
3. Temporarily block suspicious IP ranges
4. Monitor Cloud Run metrics
5. Notify GCP support

### Reporting Security Issues

**For Third-Party Discoveries:**
- Email: security@csocgolf.com (when established)
- Do not disclose publicly until fixed
- Provide steps to reproduce
- Include impact assessment

**Internal Issues:**
1. Report to project maintainers
2. Create private GitHub Issue (do not use Comments)
3. Do not commit security fixes to main without review
4. Coordinate fix and disclosure timeline

### Post-Incident Review

After any security incident:
1. Document what happened (timeline, scope, root cause)
2. What was done to contain it?
3. How to prevent recurrence?
4. Update security documentation
5. Share learnings with team

## Additional Resources

- [OWASP Top 10 Web Application Security Risks](https://owasp.org/www-project-top-ten/)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [Firebase Security Rules Documentation](https://firebase.google.com/docs/firestore/security/start)
- [OAuth 2.0 Security Best Practices](https://www.rfc-editor.org/rfc/rfc6819.html)
- [CWE Top 25](https://cwe.mitre.org/top25/) – Common security weaknesses

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-19 | 1.0 | Initial security documentation |
