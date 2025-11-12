# when-end - Technical Architecture

## System Overview

when-end is a full-stack web application for tracking events with real-time countdowns. The system consists of a React frontend, FastAPI backend, PostgreSQL database, and MinIO for file storage.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Browser                       │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │  React App  │───│  Countdown   │───│  Theme Toggle   │  │
│  │  (Vite/TS)  │   │   Timers     │   │  (Dark/Light)   │  │
│  └─────────────┘   └──────────────┘   └─────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS/HTTP
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Caddy Reverse Proxy                     │
│                    (Port 3000 / HTTPS)                       │
└───────────┬─────────────────────────────────┬───────────────┘
            │                                 │
            ▼ /api/*                          ▼ /*
┌───────────────────────┐         ┌───────────────────────────┐
│   FastAPI Backend     │         │   React Frontend (SPA)    │
│    (Port 8000)        │         │     (Port 5173)           │
│                       │         └───────────────────────────┘
│  ┌─────────────────┐ │
│  │  Auth Routes    │ │         ┌───────────────────────────┐
│  │  - Google OAuth │ │         │    PostgreSQL Database    │
│  │  - JWT Tokens   │ │◄────────│      (Port 5432)          │
│  └─────────────────┘ │         │                           │
│  ┌─────────────────┐ │         │  Tables:                  │
│  │  Event Routes   │ │         │  - users                  │
│  │  - CRUD Ops     │ │         │  - events                 │
│  │  - Attachments  │ │         │  - attachments            │
│  └─────────────────┘ │         │  - shared_events          │
│  ┌─────────────────┐ │         │  - share_tokens           │
│  │  Share Routes   │ │         └───────────────────────────┘
│  │  - Create Token │ │
│  │  - Import Event │ │         ┌───────────────────────────┐
│  └─────────────────┘ │         │    MinIO (S3 Storage)     │
│  ┌─────────────────┐ │◄────────│      (Port 9000)          │
│  │ Storage Service │ │         │                           │
│  │  - Local/S3     │ │         │  Buckets:                 │
│  │  - Signed URLs  │ │         │  - countdowns-uploads     │
│  └─────────────────┘ │         └───────────────────────────┘
└───────────────────────┘
```

## Technology Stack

### Backend

- **Framework**: FastAPI 0.104+
- **Python**: 3.11
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Auth**: Google OAuth 2.0 (Authlib)
- **Tokens**: JWT (python-jose)
- **Date/Time**: python-dateutil, pytz
- **Storage**: boto3 (S3/MinIO)
- **Testing**: pytest

### Frontend

- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix)
- **Routing**: React Router v6
- **Date Utils**: date-fns

### Infrastructure

- **Database**: PostgreSQL 15
- **Storage**: MinIO (S3-compatible)
- **Reverse Proxy**: Caddy 2
- **Container**: Docker + Docker Compose

## Core Features Implementation

### 1. Real-Time Countdowns

**Client-Side Timer**:

- `useCountdown` hook syncs with server time
- Updates every second using `setInterval`
- Calculates offset: `serverTime - clientTime`
- Prevents drift by using adjusted time

**Time Calculations**:

```typescript
const adjustedNow = new Date(Date.now() + offset);
const diff = targetDate - adjustedNow;
```

**Display Format**:

- Years, months, days, hours, minutes
- "< 1 min" for less than 60 seconds
- "Overdue" for past events

### 2. Color Bucket System

**Strict Boundaries** (in seconds):

```python
RED:     0 ≤ t < 86_400        # < 1 day
ORANGE:  86_400 ≤ t < 604_800  # 1-7 days
YELLOW:  604_800 ≤ t < 2_592_000  # 7-30 days
GREEN:   2_592_000 ≤ t < 7_776_000  # 30-90 days
CYAN:    7_776_000 ≤ t < 31_536_000  # 90-365 days
BLUE:    31_536_000 ≤ t < 94_608_000  # 1-3 years
PURPLE:  t ≥ 94_608_000  # > 3 years
```

**Computed on Read**: Not stored in database, calculated when fetching events.

### 3. Recurrence Logic

**Daily**:

```python
next_occurrence = current + timedelta(days=1)
```

**Weekly**:

```python
next_occurrence = current + timedelta(weeks=1)
```

**Monthly**:

```python
next_occurrence = current + relativedelta(months=1)
```

**Yearly** (with leap year handling):

```python
if month == 2 and day == 29:
    if is_leap_year(next_year):
        next_occurrence = (year+1, 2, 29)
    else:
        next_occurrence = (year+1, 2, 28)  # or Mar 1 based on config
```

**Next Occurrence**:

- Stored in `events.next_occurrence` column
- Updated when event is modified
- Used as `effective_due_at` for recurring events

### 4. Authentication Flow

**Google OAuth 2.0**:

1. User clicks "Sign in with Google"
2. Redirects to `/api/auth/google/login`
3. Google OAuth consent screen
4. Callback to `/api/auth/google/callback`
5. Backend creates/fetches user
6. Generates JWT tokens (access + refresh)
7. Sets HttpOnly cookies
8. Redirects to frontend

**Token Lifecycle**:

- **Access Token**: 15 minutes, stored in `access_token` cookie
- **Refresh Token**: 30 days, stored in `refresh_token` cookie
- **Rotation**: Refresh token rotated on each refresh request
- **Security**: HttpOnly, Secure (HTTPS), SameSite=Lax

**Middleware**:

```python
async def get_current_user(access_token: Cookie):
    payload = verify_access_token(access_token)
    user = db.get_user(payload['sub'])
    return user
```

### 5. File Upload System

**Storage Abstraction**:

```python
class StorageService(ABC):
    def save_file(file, filename, content_type) -> storage_key
    def delete_file(storage_key)
    def generate_signed_url(storage_key, ttl) -> url
```

**Implementations**:

- **LocalStorageService**: Saves to filesystem (`/app/uploads/`)
- **S3StorageService**: Saves to MinIO/AWS S3

**Validation**:

- **Images**: png/jpg/webp, max 10 MB
- **Videos**: mp4/webm, max 50 MB
- **MIME type**: Validated server-side
- **Size**: Checked before upload

**Signed URLs**:

- TTL: 1 hour default
- Private storage
- Generated on-demand

### 6. Event Sharing

**Share Token Generation**:

```python
token = str(uuid.uuid4())
shared_event = create_shared_event(
    payload={
        'title': event.title,
        'description': event.description,
        'event_date': event.event_date.isoformat(),
        'repeat_interval': event.repeat_interval,
        'has_attachments': bool(event.attachments),
    }
)
share_token = create_token(shared_event.id, token)
```

**Import Flow**:

1. User receives share link: `/share/{token}`
2. Preview page shows event details (public)
3. "Add to My Events" button (requires auth)
4. Creates new event for current user
5. Optionally copies attachments

**Security**:

- Tokens are UUIDs (non-guessable)
- Optional expiration date
- Attachments NOT copied by default

## Database Schema

### users

```sql
id              UUID PRIMARY KEY
email           VARCHAR(255) UNIQUE NOT NULL
name            VARCHAR(255) NOT NULL
avatar_url      VARCHAR(500)
oauth_provider  VARCHAR(50) NOT NULL
oauth_sub       VARCHAR(255) NOT NULL
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE
```

### events

```sql
id              UUID PRIMARY KEY
user_id         UUID FOREIGN KEY (users.id) ON DELETE CASCADE
title           VARCHAR(120) NOT NULL
description     TEXT
event_date      TIMESTAMP WITH TIME ZONE NOT NULL
repeat_interval ENUM('none','day','week','month','year') DEFAULT 'none'
next_occurrence TIMESTAMP WITH TIME ZONE
timezone        VARCHAR(100)
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE

INDEX idx_user_id (user_id)
```

### attachments

```sql
id          UUID PRIMARY KEY
event_id    UUID FOREIGN KEY (events.id) ON DELETE CASCADE
kind        ENUM('image','video') NOT NULL
storage_key VARCHAR(500) NOT NULL
mime        VARCHAR(100) NOT NULL
size        INTEGER NOT NULL
width       INTEGER
height      INTEGER
duration    INTEGER
created_at  TIMESTAMP WITH TIME ZONE
updated_at  TIMESTAMP WITH TIME ZONE

INDEX idx_event_id (event_id)
```

### shared_events

```sql
id                          UUID PRIMARY KEY
owner_user_id               UUID FOREIGN KEY (users.id) ON DELETE CASCADE
payload                     JSONB NOT NULL
include_attachments_default BOOLEAN DEFAULT FALSE
created_at                  TIMESTAMP WITH TIME ZONE
updated_at                  TIMESTAMP WITH TIME ZONE

INDEX idx_owner_user_id (owner_user_id)
```

### share_tokens

```sql
id              UUID PRIMARY KEY
shared_event_id UUID FOREIGN KEY (shared_events.id) ON DELETE CASCADE
token           VARCHAR(255) UNIQUE NOT NULL
expires_at      TIMESTAMP WITH TIME ZONE
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE

INDEX idx_token (token)
INDEX idx_shared_event_id (shared_event_id)
```

## API Endpoints

### Authentication

```
GET  /api/auth/google/login      → Redirect to Google OAuth
GET  /api/auth/google/callback   → Handle OAuth callback
POST /api/auth/refresh           → Refresh access token
POST /api/auth/logout            → Clear session
GET  /api/auth/me                → Get current user
```

### Events

```
POST   /api/events                → Create event
GET    /api/events                → List events (query: q, include_overdue, limit, offset)
GET    /api/events/{id}           → Get event details
PUT    /api/events/{id}           → Update event
DELETE /api/events/{id}           → Delete event
POST   /api/events/{id}/attachments        → Upload attachment
DELETE /api/events/{id}/attachments/{aid}  → Delete attachment
```

### Sharing

```
POST /api/events/{id}/share     → Create share token
GET  /api/share/{token}          → Preview shared event (public)
POST /api/share/{token}/import   → Import event to user's list
```

## Security Measures

1. **Authentication**: Google OAuth 2.0 only
2. **Authorization**: Users can only access/modify their own events
3. **CORS**: Restricted to frontend origin
4. **Cookies**: HttpOnly, Secure, SameSite=Lax
5. **Input Validation**: Pydantic schemas with strict validation
6. **SQL Injection**: SQLAlchemy ORM (parameterized queries)
7. **XSS**: React auto-escapes content
8. **CSRF**: SameSite cookies + origin validation
9. **File Upload**: Size and MIME type validation
10. **Private Storage**: Signed URLs with TTL

## Performance Optimizations

1. **Database Indexes**: On foreign keys and frequently queried columns
2. **Connection Pooling**: SQLAlchemy pool management
3. **Pagination**: Cursor-based pagination (ready for large datasets)
4. **Client-Side Caching**: React state management
5. **CDN-Ready**: Static assets can be served from CDN
6. **Lazy Loading**: Images and videos loaded on-demand

## Testing Strategy

### Unit Tests (Backend)

- Color bucket boundary tests
- Recurrence calculation tests
- Leap year handling tests
- Remaining seconds calculation

### Integration Tests

- Auth flow (login, refresh, logout)
- Event CRUD operations
- Share token creation and import
- File upload and validation

### Load Tests

- List 1000+ events with sorting
- Concurrent user requests
- Database query performance

## Deployment Considerations

### Development

- Docker Compose with hot-reload
- Local storage for files
- Debug mode enabled
- Verbose logging

### Production

- HTTPS via Caddy + Let's Encrypt
- MinIO or AWS S3 for storage
- PostgreSQL with backups
- Error tracking (Sentry)
- Log aggregation
- Health check endpoints
- Rate limiting
- CDN for static assets

## Future Enhancements

1. **Notifications**: Email/push notifications for upcoming events
2. **Tags**: Categorize events with tags
3. **Filters**: Filter by tag, date range, color bucket
4. **Calendar View**: Monthly/weekly calendar display
5. **Export**: Export events to ICS format
6. **Collaboration**: Shared event lists between users
7. **Thumbnails**: Auto-generate image thumbnails
8. **Video Previews**: Generate video poster frames
9. **Mobile App**: Native iOS/Android apps
10. **Analytics**: Event statistics and insights

## Monitoring & Observability

**Health Checks**:

- `/api/health` - Application health
- Database connectivity
- Storage service availability

**Metrics** (to implement):

- Request latency (p50, p95, p99)
- Error rates
- Active users
- Event creation rate
- Storage usage

**Logging**:

- Structured JSON logs
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging
- Error stack traces

## Scalability

**Horizontal Scaling**:

- Stateless backend (can run multiple instances)
- Load balancer in front of backend
- Shared database and storage

**Vertical Scaling**:

- Database: Increase PostgreSQL resources
- Cache: Add Redis for session storage
- Storage: Distribute across multiple S3 buckets

**Bottlenecks**:

- Database queries (add indexes as needed)
- File uploads (consider direct S3 uploads)
- Real-time features (consider WebSockets for live updates)

---

## Summary

Countdowns is a production-ready MVP built with modern web technologies. The architecture is clean, secure, and scalable. The codebase follows best practices with proper separation of concerns, comprehensive error handling, and extensive validation.

Key strengths:

- ✅ Real-time countdown synchronization
- ✅ Robust recurrence logic with leap year handling
- ✅ Secure authentication and authorization
- ✅ Flexible storage abstraction
- ✅ Clean API design with comprehensive validation
- ✅ Responsive, accessible UI
- ✅ Docker-based deployment
- ✅ Comprehensive test coverage

The application is ready for deployment and can easily be extended with additional features as needed.
