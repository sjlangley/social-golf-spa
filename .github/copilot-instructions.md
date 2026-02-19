# GitHub Copilot Instructions

Project-specific guidance for GitHub Copilot when working on the Caringbah Social Golf Club management system.

## Stack Summary

**Frontend:**
- React 19 with TypeScript
- Vite for build tooling
- TanStack Query for data fetching
- React Router for routing
- Google Identity Services for authentication

**Backend:**
- FastAPI (Python 3.12+)
- Firebase Admin SDK for auth verification
- Pydantic v2 for data validation
- Deployed to Google Cloud Run (serverless)

**Database:**
- Google Cloud Firestore (Native mode)
- Document-based NoSQL

**Auth:**
- Google OAuth 2.0 via Google Identity Services (frontend)
- ID token verification via Firebase Admin SDK (backend)
- Role-based authorization (admin/member)

## File Structure Expectations

This is a **monorepo** with three independent applications deployed as separate services.

### Monorepo Layout
```
csocgolf-v2 (monorepo root)
├── apps/
│   ├── golf-ui/                # React SPA (Node.js)
│   │   ├── src/
│   │   ├── tests/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   ├── golf-api/               # FastAPI backend (Python)
│   │   ├── app/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   └── .env.example
│   └── handicap-calculator/    # Pub/Sub subscriber service (Python)
│       ├── app/
│       ├── tests/
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── .env.example
├── docs/
│   └── architecture.md         # Architecture documentation
└── .github/
    ├── workflows/              # CI/CD workflows
    └── copilot-instructions.md # This file
```

### Frontend Structure (apps/golf-ui)

```
apps/golf-ui/
├── src/
│   ├── main.tsx             # App entry point
│   ├── App.tsx              # Root component
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   ├── members/
│   │   │   ├── MemberList.tsx
│   │   │   └── MemberDetails.tsx
│   │   ├── matches/
│   │   │   ├── MatchList.tsx
│   │   │   ├── MatchDetails.tsx
│   │   │   └── RecordMatchForm.tsx
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       └── Spinner.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── MembersPage.tsx
│   │   ├── MatchesPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts       # Auth context and hook
│   │   ├── useMembers.ts    # TanStack Query hooks for members
│   │   ├── useMatches.ts    # TanStack Query hooks for matches
│   │   └── useScores.ts     # TanStack Query hooks for scores
│   ├── api/
│   │   ├── client.ts        # Axios client with auth interceptor
│   │   ├── members.ts       # Member API functions
│   │   ├── matches.ts       # Match API functions
│   │   └── types.ts         # TypeScript types for API responses
│   ├── contexts/
│   │   └── AuthContext.tsx  # Auth state management
│   └── utils/
│       ├── format.ts        # Date/number formatting
│       └── constants.ts     # App-wide constants
├── tests/
│   └── setup.ts
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env.example
```

### Backend Structure (apps/golf-api)

```
apps/golf-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration and environment variables
│   ├── models.py            # Pydantic models (request/response)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── middleware.py    # Token verification middleware
│   │   └── dependencies.py  # Auth dependencies (get_current_user, require_admin)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── members.py       # Member CRUD endpoints
│   │   ├── matches.py       # Match CRUD endpoints
│   │   ├── scores.py        # Score CRUD endpoints
│   │   ├── clubs.py         # Club/course/tee endpoints
│   │   └── health.py        # Health check endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── firestore.py     # Firestore client wrapper
│   │   ├── pubsub.py        # Pub/Sub publisher for score events
│   │   └── match.py         # Match result processing
│   └── utils/
│       ├── __init__.py
│       ├── logging.py       # Structured logging setup
│       └── request_id.py    # Request ID middleware
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── pyproject.toml           # Python project configuration & dependencies
├── Dockerfile
└── .env.example
```

### Handicap Calculator Structure (apps/handicap-calculator)

```
apps/handicap-calculator/
├── app/
│   ├── __init__.py
│   ├── main.py              # Cloud Run HTTP endpoint
│   ├── config.py            # Configuration and environment variables
│   ├── models.py            # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── firestore.py     # Firestore client wrapper
│       ├── pubsub.py        # Pub/Sub subscription handler
│       └── handicap.py      # Handicap calculation logic
├── tests/
│   ├── unit/
│   └── conftest.py
├── pyproject.toml           # Python project configuration & dependencies
├── Dockerfile
└── .env.example
```

## Coding Conventions

### TypeScript (Frontend)

**Naming:**
- Components: `PascalCase` (e.g., `MemberList.tsx`)
- Hooks: `camelCase` with `use` prefix (e.g., `useMembers.ts`)
- Types/Interfaces: `PascalCase` (e.g., `Member`, `MatchResult`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`)
- Functions: `camelCase` (e.g., `formatDate`)

**Component Style:**
- Prefer function components over class components
- Use TypeScript, not PropTypes
- Export named components (not default exports)
- Co-locate types with components when component-specific

**Example Component:**
```typescript
// MemberList.tsx
import { useMembers } from '@/hooks/useMembers';
import { Member } from '@/api/types';

interface MemberListProps {
  showInactive?: boolean;
}

export function MemberList({ showInactive = false }: MemberListProps) {
  const { data: members, isLoading, error } = useMembers({ inactive: showInactive });

  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className="member-list">
      {members?.map((member) => (
        <MemberCard key={member.id} member={member} />
      ))}
    </div>
  );
}
```

**API Client Pattern:**
```typescript
// api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

// Intercept requests to add auth token
apiClient.interceptors.request.use((config) => {
  const token = getIdToken(); // From auth context
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export { apiClient };
```

**TanStack Query Usage:**
```typescript
// hooks/useMembers.ts
import { useQuery } from '@tanstack/react-query';
import { fetchMembers } from '@/api/members';

export function useMembers(filters?: { inactive?: boolean }) {
  return useQuery({
    queryKey: ['members', filters],
    queryFn: () => fetchMembers(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

## Pub/Sub Message Format (Score Events)

When a score is recorded in `golf-api`, a Pub/Sub message is published to topic `score.created`:

```json
{
  "event": "score.created",
  "memberId": "member123",
  "scoreId": "score456",
  "teeId": "tee789",
  "date": "2024-01-15T10:30:00Z",
  "scratch": 85,
  "nett": 72,
  "timestamp": "2024-01-15T10:32:15Z"
}
```

The `handicap-calculator` service subscribes to this topic and:
1. Fetches member's last 20 scores
2. Calculates new handicap using Australian Golf standards
3. Updates member's handicap in Firestore
4. Logs completion with request ID for tracing

### Python (Backend & Handicap Calculator)

**Naming:**
- Modules: `snake_case` (e.g., `member_routes.py`)
- Classes: `PascalCase` (e.g., `MemberService`)
- Functions: `snake_case` (e.g., `calculate_handicap`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_HANDICAP`)
- Private functions: prefix with `_` (e.g., `_validate_score`)

**Type Hints:**
- Use type hints for all function parameters and return types
- Use Pydantic models for request/response bodies
- Use `typing` module for complex types

**Example Route Handler:**
```python
# routes/members.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Member, MemberCreate, MemberUpdate
from app.auth.dependencies import get_current_user, require_admin
from app.services.firestore import FirestoreService

router = APIRouter(prefix="/api/v1/members", tags=["members"])

@router.get("/", response_model=list[Member])
async def list_members(
    inactive: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: FirestoreService = Depends(get_firestore),
):
    """List all members. Public endpoint."""
    members = await db.list_members(inactive=inactive, page=page, page_size=page_size)
    return members

@router.post("/", response_model=Member, status_code=status.HTTP_201_CREATED)
async def create_member(
    member: MemberCreate,
    user=Depends(require_admin),
    db: FirestoreService = Depends(get_firestore),
):
    """Create a new member. Requires admin role."""
    return await db.create_member(member)
```

**Service Pattern:**
```python
# services/firestore.py
from google.cloud import firestore
from app.models import Member, MemberCreate

class FirestoreService:
    def __init__(self):
        self.client = firestore.Client()

    async def list_members(
        self,
        inactive: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> list[Member]:
        """Fetch members from Firestore with pagination."""
        query = self.client.collection('members')

        if not inactive:
            query = query.where('inactive', '==', False)

        query = query.order_by('memberNo')
        query = query.limit(page_size)
        query = query.offset((page - 1) * page_size)

        docs = query.stream()
        return [Member(**doc.to_dict(), id=doc.id) for doc in docs]

    async def create_member(self, member: MemberCreate) -> Member:
        """Create a new member in Firestore."""
        doc_ref = self.client.collection('members').document()
        member_dict = member.model_dump()
        member_dict['createdAt'] = firestore.SERVER_TIMESTAMP
        doc_ref.set(member_dict)

        # Fetch the created document to get server timestamp
        created_doc = doc_ref.get()
        return Member(**created_doc.to_dict(), id=created_doc.id)
```

**Error Handling:**
```python
# Always use HTTPException for API errors
from fastapi import HTTPException, status

if not member_exists:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Member with ID {member_id} not found"
    )
```

**Logging:**
```python
import logging
import json

logger = logging.getLogger(__name__)

# Use structured logging
logger.info("Member created", extra={
    "member_id": member.id,
    "user": user.email,
    "request_id": request_id,
})
```

## Testing Expectations

### Frontend Tests

**Unit Tests (Vitest):**
- Test utility functions in isolation
- Test custom hooks with `@testing-library/react-hooks`
- Test components with `@testing-library/react`
- Mock API calls with MSW (Mock Service Worker)

**Example:**
```typescript
// MemberList.test.tsx
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemberList } from './MemberList';

describe('MemberList', () => {
  it('renders loading state', () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemberList />
      </QueryClientProvider>
    );
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders member list', async () => {
    // Test with mocked API response
    // ...
  });
});
```

### Backend Tests

**Unit Tests (pytest):**
- Test service functions in isolation
- Test route handlers with mock dependencies
- Test auth middleware
- Test handicap calculation logic

**Example:**
```python
# tests/unit/test_members.py
import pytest
from app.services.handicap import calculate_handicap
from app.models import Score

def test_calculate_handicap_with_fewer_than_20_scores():
    """Should use best 1 of 5 scores."""
    scores = [
        Score(differential=10.5, date="2024-01-01"),
        Score(differential=12.3, date="2024-01-08"),
        Score(differential=9.8, date="2024-01-15"),
        Score(differential=11.2, date="2024-01-22"),
        Score(differential=10.1, date="2024-01-29"),
    ]

    handicap = calculate_handicap(scores)

    # Best score is 9.8, multiplied by 0.93
    assert handicap == pytest.approx(9.1, abs=0.1)

@pytest.mark.asyncio
async def test_list_members_excludes_inactive(mock_firestore):
    """Should not return inactive members by default."""
    service = FirestoreService(client=mock_firestore)
    members = await service.list_members(inactive=False)

    assert all(not m.inactive for m in members)
```

**Integration Tests:**
- Test full API endpoints with test Firestore instance
- Test auth flow with test tokens
- Test error handling

## Firestore Access Patterns

### Reading Data

**Single Document:**
```python
doc_ref = firestore_client.collection('members').document(member_id)
doc = doc_ref.get()

if not doc.exists:
    raise HTTPException(status_code=404, detail="Member not found")

member = Member(**doc.to_dict(), id=doc.id)
```

**Query Collection:**
```python
# Query with filters
query = (
    firestore_client.collection('scores')
    .where('memberId', '==', member_id)
    .order_by('date', direction=firestore.Query.DESCENDING)
    .limit(20)
)

docs = query.stream()
scores = [Score(**doc.to_dict(), id=doc.id) for doc in docs]
```

**Pagination:**
```python
# First page
query = collection.order_by('date').limit(page_size)
docs = list(query.stream())

# Next page
if docs:
    last_doc = docs[-1]
    next_query = query.start_after(last_doc)
    next_docs = list(next_query.stream())
```

### Writing Data

**Create:**
```python
doc_ref = firestore_client.collection('members').document()
doc_ref.set({
    'firstName': 'John',
    'lastName': 'Doe',
    'createdAt': firestore.SERVER_TIMESTAMP,
})
return doc_ref.id
```

**Update:**
```python
doc_ref = firestore_client.collection('members').document(member_id)
doc_ref.update({
    'email': 'new@example.com',
    'updatedAt': firestore.SERVER_TIMESTAMP,
})
```

**Delete:**
```python
doc_ref = firestore_client.collection('members').document(member_id)
doc_ref.delete()
```

**Batch Writes (for multiple operations):**
```python
batch = firestore_client.batch()

# Create multiple documents in one batch
for score_data in scores:
    doc_ref = firestore_client.collection('scores').document()
    batch.set(doc_ref, score_data)

batch.commit()
```

### Common Pitfalls

**❌ Don't:**
- Use Firestore transactions for simple reads/writes (adds latency)
- Query without indexes (will fail in production)
- Store large arrays (> 100 items) in a single document
- Use client-side timestamps (use `firestore.SERVER_TIMESTAMP`)

**✅ Do:**
- Create composite indexes for complex queries
- Use subcollections for one-to-many relationships with high cardinality
- Paginate list queries
- Handle `DocumentSnapshot.exists` before accessing data
- Use batch writes for multiple related operations

## Auth Verification Rules

### Frontend: Never Trust Client-Side Auth

**❌ Wrong:**
```typescript
// Don't check role on frontend to hide UI elements
{user.role === 'admin' && <AdminButton />}
// This is security through obscurity - backend must still verify
```

**✅ Correct:**
```typescript
// Hide UI for UX, but backend enforces access control
{user.role === 'admin' && <AdminButton />}
// Backend will return 403 if user is not actually an admin
```

### Backend: Always Verify Token and Check Role

**Required Pattern:**
```python
from fastapi import Depends, HTTPException, status
from app.auth.dependencies import require_admin

@router.post("/members")
async def create_member(
    member: MemberCreate,
    user = Depends(require_admin),  # This checks token AND role
):
    # user is guaranteed to be authenticated admin here
    ...
```

**Auth Dependency Implementation:**
```python
# auth/dependencies.py
from fastapi import Depends, HTTPException, Header, status
from firebase_admin import auth

async def get_current_user(authorization: str = Header(None)):
    """Extract and verify ID token from Authorization header."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.split('Bearer ')[1]

    try:
        # Verify token with Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        email = decoded_token.get('email')

        # Fetch user from Firestore to get role
        user_doc = firestore_client.collection('users').document(user_id).get()

        if not user_doc.exists:
            # First time login - create user with default role
            role = 'admin' if is_first_user() else 'member'
            create_user(user_id, email, role)
        else:
            role = user_doc.get('role')

        return {'id': user_id, 'email': email, 'role': role}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

def require_admin(user = Depends(get_current_user)):
    """Require user to have admin role."""
    if user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
```

### Security Checklist

Before merging any PR that touches authentication/authorization:

- [ ] All protected endpoints use `Depends(get_current_user)` or `Depends(require_admin)`
- [ ] Token is verified using Firebase Admin SDK (never trust client claims)
- [ ] Role is fetched from Firestore (never trust token claims for authorization)
- [ ] Sensitive operations (create/update/delete) require admin role
- [ ] Error messages don't leak sensitive information
- [ ] Tokens are not logged or stored
- [ ] Tests verify auth is enforced (try calling endpoint without token)

## When Unsure, Ask

If you encounter any of these situations, **stop and ask for clarification**:

1. **Authorization Ambiguity**
   - Is this endpoint public, member-only, or admin-only?
   - Should users be able to edit their own data but not others'?

2. **Business Logic Questions**
   - How should handicaps be calculated for edge cases (< 5 scores)?
   - What happens if a match date is in the future?
   - Should inactive members be included in match results?

3. **Data Model Questions**
   - Should this be a separate collection or a subcollection?
   - What should happen if a referenced document (e.g., tee) is deleted?
   - Should we store computed values (e.g., nett score) or calculate on demand?

4. **UX/UI Questions**
   - Should this action require confirmation?
   - What should the loading state look like?
   - Should this be a modal or a separate page?

5. **Performance Questions**
   - Should this query be paginated?
   - Is this query pattern efficient for Firestore?
   - Should we cache this response?

6. **Deployment/Infrastructure**
   - Should this be a separate Cloud Run service?
   - What environment variable should this use?
   - Where should this secret be stored?

**Don't guess or assume** - ping the team for clarification. It's faster than refactoring later.

## Code Review Standards

When reviewing code (or generating code):

- **Working code only** - No placeholder functions or TODOs
- **Type safety** - All TypeScript/Python code is fully typed
- **Error handling** - All error cases are handled gracefully
- **Tests included** - New features have corresponding tests
- **Consistent style** - Follows conventions in this document
- **Logging added** - Important operations are logged
- **Auth enforced** - Protected endpoints verify token and role
- **Documentation updated** - README and architecture.md reflect changes

## Common Patterns

### Handicap Calculation
```python
# services/handicap.py
from app.models import Score

def calculate_handicap(scores: list[Score]) -> float:
    """
    Calculate handicap using Australian Golf standards.

    Uses best N of last 20 scores, where N depends on score count:
    - < 6 scores: best 1
    - 6-8 scores: best 2
    - 9-11 scores: best 3
    - 12-14 scores: best 4
    - 15-16 scores: best 5
    - 17-18 scores: best 6
    - 19 scores: best 7
    - 20+ scores: best 8

    Handicap = (average of best N) * 0.93
    """
    if len(scores) == 0:
        return 0.0

    count_map = {
        range(0, 6): 1,
        range(6, 9): 2,
        range(9, 12): 3,
        range(12, 15): 4,
        range(15, 17): 5,
        range(17, 19): 6,
        range(19, 20): 7,
    }

    score_count = min(len(scores), 20)
    n = 8  # default for 20+ scores

    for range_obj, count in count_map.items():
        if score_count in range_obj:
            n = count
            break

    # Sort scores by differential (lowest first)
    sorted_scores = sorted(scores[-20:], key=lambda s: s.differential)

    # Take best N scores
    best_scores = sorted_scores[:n]
    average = sum(s.differential for s in best_scores) / n

    # Apply 0.93 multiplier and round to 1 decimal
    return round(average * 0.93, 1)
```

### API Error Response
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with structured error response."""
    request_id = request.state.request_id

    logger.error(
        "Unhandled exception",
        extra={
            "error": str(exc),
            "request_id": request_id,
            "path": request.url.path,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "requestId": request_id,
            }
        },
    )
```

### Frontend API Hook Pattern
```typescript
// hooks/useCreateMember.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createMember } from '@/api/members';
import type { MemberCreate } from '@/api/types';

export function useCreateMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (member: MemberCreate) => createMember(member),
    onSuccess: () => {
      // Invalidate members list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['members'] });
    },
    onError: (error) => {
      console.error('Failed to create member:', error);
      // Could also show toast notification here
    },
  });
}

// Usage in component:
function AddMemberForm() {
  const createMember = useCreateMember();

  const handleSubmit = (data: MemberCreate) => {
    createMember.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button type="submit" disabled={createMember.isPending}>
        {createMember.isPending ? 'Creating...' : 'Create Member'}
      </button>
    </form>
  );
}
```

## Glossary

**Golf Terms:**
- **Handicap** – A numerical measure of a golfer's potential ability
- **Differential** – A score adjusted for course difficulty (slope rating)
- **Scratch Score** – Gross score (actual strokes taken)
- **Nett Score** – Score minus handicap strokes
- **Stableford Points** – Scoring system based on points per hole
- **AMCR** – Australian Men's Course Rating
- **Slope Rating** – Measure of course difficulty for bogey golfers vs scratch golfers
- **Par** – Expected number of strokes for a hole or course
- **Tee** – Starting point for a hole (different tees have different distances/ratings)

**Technical Terms:**
- **ID Token** – JWT issued by Google after successful authentication
- **Service Account** – GCP identity used by backend to access Firestore
- **Firestore** – Google's NoSQL document database
- **Cloud Run** – Serverless container platform
- **TanStack Query** – React library for async state management (formerly React Query)
- **Vite** – Modern frontend build tool (faster than webpack)
