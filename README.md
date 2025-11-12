# when-end - Event Tracking with Real-Time Countdowns

A production-ready web application for tracking events with real-time countdowns, Google authentication, event sharing, and rich media attachments.

## Features

- 🎯 **Real-time Countdowns** - Track time remaining with live updates
- 🎨 **Color-coded Events** - Visual buckets (Red, Orange, Yellow, Green, Cyan, Blue, Purple)
- 🔄 **Recurring Events** - Daily, weekly, monthly, yearly repetition with leap year handling
- 🔗 **Event Sharing** - Share via secure links, import to own collection
- 📎 **Rich Attachments** - Images and videos with thumbnails
- 🌙 **Dark/Light Theme** - Persistent theme preference
- 🔐 **Google OAuth** - Secure authentication with refresh token rotation
- 🌍 **Timezone Support** - UTC storage, local display (default: Europe/Warsaw)

## Tech Stack

**Backend:**

- Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic
- PostgreSQL (UTC timestamps)
- Google OAuth 2.0 (Authlib)
- JWT authentication (access + refresh with rotation)
- MinIO (S3-compatible storage)

**Frontend:**

- React 18 + Vite + TypeScript
- Tailwind CSS + shadcn/ui (Radix)
- Real-time countdown hooks

**Infrastructure:**

- Docker Compose
- Caddy reverse proxy (HTTPS)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Google OAuth credentials (see below)

### 1. Clone and Setup

```bash
cd when_ending
cp ops/.env.example .env
```

### 2. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:3000/api/auth/google/callback`
6. Copy Client ID and Secret to `.env`:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### 3. Generate JWT Secrets

```bash
# Linux/Mac
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For JWT_REFRESH_SECRET_KEY

# Windows (PowerShell)
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

Add to `.env`:

```env
JWT_SECRET_KEY=your_generated_secret
JWT_REFRESH_SECRET_KEY=your_generated_refresh_secret
```

### 4. Start Services

```bash
docker compose up -d
```

This will:

- Start PostgreSQL on port 5432
- Start MinIO on port 9000 (console: 9001)
- Run Alembic migrations
- Start backend on port 8000
- Start frontend on port 5173
- Setup Caddy reverse proxy on port 3000

### 5. Access Application

Open browser: **http://localhost:3000**

- Frontend: http://localhost:3000
- Backend API: http://localhost:3000/api
- API Docs: http://localhost:3000/api/docs
- MinIO Console: http://localhost:9001 (admin/minioadmin)

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

## Project Structure

```
when_ending/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Config, security, dependencies
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── repositories/  # Data access layer
│   │   └── main.py        # FastAPI app
│   ├── alembic/           # Database migrations
│   ├── tests/             # Pytest tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks (countdown, theme)
│   │   ├── lib/           # API client, utils
│   │   ├── pages/         # Route pages
│   │   └── App.tsx
│   ├── public/
│   └── package.json
├── ops/
│   ├── Caddyfile
│   └── .env.example
└── docker-compose.yml
```

## API Documentation

### Authentication

- `GET /api/auth/google/login` - Redirect to Google OAuth
- `GET /api/auth/google/callback` - OAuth callback (sets cookies)
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Clear session
- `GET /api/auth/me` - Get current user

### Events

- `POST /api/events` - Create event
- `GET /api/events` - List events (query: `q`, `include_overdue`, pagination)
- `GET /api/events/{id}` - Get event details
- `PUT /api/events/{id}` - Update event
- `DELETE /api/events/{id}` - Delete event
- `POST /api/events/{id}/attachments` - Upload attachment
- `DELETE /api/events/{id}/attachments/{att_id}` - Delete attachment

### Sharing

- `POST /api/events/{id}/share` - Create share token
- `GET /api/share/{token}` - Preview shared event
- `POST /api/share/{token}/import` - Import to user's events

## Color Bucket Logic

Events are color-coded based on time remaining:

| Color  | Time Remaining         |
| ------ | ---------------------- |
| RED    | < 1 day (< 86,400 sec) |
| ORANGE | 1-7 days               |
| YELLOW | 7-30 days              |
| GREEN  | 30-90 days             |
| CYAN   | 90-365 days            |
| BLUE   | 1-3 years              |
| PURPLE | > 3 years              |

Overdue events (time < 0) appear in "Finished" tab with no color bucket.

## Recurrence Rules

- **Daily**: Next occurrence = current + 1 day
- **Weekly**: Next occurrence = current + 7 days
- **Monthly**: Next occurrence = same day next month
- **Yearly**: Next occurrence = same MM-DD next year
  - Feb 29 → Feb 28 in non-leap years (configurable: `leap_policy="feb28"`)

## Security

- **Authentication**: Google OAuth 2.0 with JWT tokens
- **Access Token**: 15 minutes (HttpOnly cookie)
- **Refresh Token**: 30 days with rotation
- **CORS**: Restricted to frontend origin
- **File Upload**: Size & MIME type validation
- **Authorization**: Users own only their events
- **Secure Cookies**: HttpOnly, Secure (HTTPS), SameSite=Lax

## Environment Variables

See `ops/.env.example` for all configuration options:

- `DATABASE_URL` - PostgreSQL connection string
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - OAuth credentials
- `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY` - Token signing keys
- `FRONTEND_URL` - CORS origin
- `STORAGE_TYPE` - `local` or `s3`
- `S3_*` - MinIO/S3 configuration

## Production Deployment

1. **Update `.env`**:

   - Set `ENVIRONMENT=production`
   - Use strong JWT secrets
   - Configure HTTPS domain in `FRONTEND_URL`, `BACKEND_URL`
   - Setup production database
   - Configure S3/MinIO with proper credentials

2. **Update Caddyfile** with your domain

3. **Deploy**:

```bash
docker compose -f docker-compose.prod.yml up -d
```

4. **Run migrations**:

```bash
docker compose exec backend alembic upgrade head
```

## License

MIT

## Support

For issues and questions, please open a GitHub issue.
