# when-end - Quick Start Guide

## 🚀 Getting Started

This guide will help you set up and run the when-end application locally.

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Git (to clone the repository)
- A Google Cloud account (for OAuth)

### Step 1: Google OAuth Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project** (or select an existing one)
3. **Enable Google+ API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application"
   - Add authorized redirect URI: `http://localhost:3000/api/auth/google/callback`
   - Click "Create"
5. **Copy your credentials**:
   - Copy the Client ID and Client Secret

### Step 2: Environment Configuration

Create a `.env` file in the root directory:

```bash
cp ops/.env.example .env
```

Edit `.env` and set the following required variables:

```env
# Google OAuth (REQUIRED)
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here

# JWT Secrets (REQUIRED - generate with commands below)
JWT_SECRET_KEY=your_generated_secret_key_here
JWT_REFRESH_SECRET_KEY=your_generated_refresh_secret_key_here
```

**Generate JWT Secrets:**

On Linux/Mac:

```bash
openssl rand -hex 32
```

On Windows PowerShell:

```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

### Step 3: Start the Application

```bash
# Start all services
docker compose up -d

# Check logs
docker compose logs -f

# Or start individual services
docker compose up backend frontend db minio caddy
```

This will start:

- PostgreSQL on port 5432
- MinIO on port 9000 (console: 9001)
- Backend API on port 8000
- Frontend on port 5173
- Caddy reverse proxy on port 3000

### Step 4: Access the Application

Open your browser and navigate to:

**http://localhost:3000**

The application should be running! Sign in with Google to start creating events.

### Additional URLs

- **API Documentation**: http://localhost:3000/api/docs
- **MinIO Console**: http://localhost:9001 (login: minioadmin/minioadmin)
- **Direct Backend**: http://localhost:8000
- **Direct Frontend**: http://localhost:5173

## 🛠️ Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env in backend folder or export)
export DATABASE_URL=postgresql://when_end:when_end_password@localhost:5432/when_end_db
export GOOGLE_CLIENT_ID=your_id
export GOOGLE_CLIENT_SECRET=your_secret
export JWT_SECRET_KEY=your_key
export JWT_REFRESH_SECRET_KEY=your_refresh_key

# Run migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Run Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_event_service.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## 🔍 Troubleshooting

### Issue: "Google OAuth not configured"

**Solution**: Make sure you've set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your `.env` file and restarted the containers.

```bash
docker compose restart backend
```

### Issue: "Database connection failed"

**Solution**: Ensure PostgreSQL is running and accessible:

```bash
# Check if database container is running
docker compose ps db

# Check database logs
docker compose logs db

# Restart database
docker compose restart db
```

### Issue: "Cannot connect to MinIO"

**Solution**: Make sure MinIO is running:

```bash
docker compose ps minio
docker compose logs minio
docker compose restart minio
```

### Issue: Frontend shows "Network Error"

**Solution**: Ensure backend is running and accessible:

```bash
# Check backend logs
docker compose logs backend

# Check if backend is responding
curl http://localhost:8000/api/health
```

### Issue: "Module not found" errors in frontend

**Solution**: Install node modules:

```bash
cd frontend
npm install
```

### Clear Everything and Start Fresh

```bash
# Stop all containers
docker compose down

# Remove volumes (WARNING: This deletes all data!)
docker compose down -v

# Rebuild images
docker compose build --no-cache

# Start fresh
docker compose up -d
```

## 📊 Understanding Color Buckets

Events are color-coded based on time remaining:

| Color     | Time Range  | Description                |
| --------- | ----------- | -------------------------- |
| 🔴 RED    | < 1 day     | Urgent! Less than 24 hours |
| 🟠 ORANGE | 1-7 days    | Coming up this week        |
| 🟡 YELLOW | 7-30 days   | Coming up this month       |
| 🟢 GREEN  | 30-90 days  | Coming up this quarter     |
| 🔵 CYAN   | 90-365 days | Coming up this year        |
| 🔷 BLUE   | 1-3 years   | Long-term event            |
| 🟣 PURPLE | > 3 years   | Very long-term             |

Overdue events (past their due date) appear in the "Finished" tab with no color.

## 🔄 Recurring Events

The app supports recurring events with smart date calculations:

- **Daily**: Repeats every day
- **Weekly**: Repeats same day of week
- **Monthly**: Repeats same day of month
- **Yearly**: Repeats same date each year
  - Special case: Feb 29 defaults to Feb 28 in non-leap years

## 🔗 Sharing Events

To share an event:

1. Click the **Share** button on any event
2. A share link is copied to your clipboard
3. Send the link to anyone
4. They can preview the event and add it to their own countdown list

**Note**: Attachments are NOT copied by default for privacy. Recipients can opt-in to copy attachments when importing.

## 🎨 Theme Toggle

Click the sun/moon icon in the header to switch between light and dark themes. Your preference is saved automatically.

## 📱 Mobile Friendly

The app is fully responsive and works great on mobile devices!

## 🔐 Security Features

- **Google OAuth 2.0** for secure authentication
- **JWT tokens** with automatic refresh (15-minute access, 30-day refresh)
- **HttpOnly cookies** to prevent XSS attacks
- **CSRF protection** via SameSite cookies
- **File validation** for uploads (size and type)
- **Private attachments** with signed URLs

## 📈 Performance Tips

- Events are sorted by remaining time automatically
- Server-synchronized countdown timers prevent drift
- Pagination ready (100 events per page by default)
- Efficient database indexes on frequently queried fields

## 🌍 Timezone Support

- All dates stored in UTC in the database
- Display timezone defaults to Europe/Warsaw
- Can be customized per event
- Client displays times in local timezone

## 🎯 Feature Checklist

- ✅ Google OAuth authentication
- ✅ Create/edit/delete events
- ✅ Real-time countdown timers
- ✅ Color-coded time buckets
- ✅ Recurring events (daily/weekly/monthly/yearly)
- ✅ Search events by title
- ✅ Share events via link
- ✅ Upload images and videos
- ✅ Dark/light theme
- ✅ Upcoming/Finished tabs
- ✅ Mobile responsive design

## 🚀 Production Deployment

For production deployment:

1. **Update environment variables**:

   - Set `ENVIRONMENT=production`
   - Use strong, unique secrets
   - Configure production database
   - Set up proper domain in `FRONTEND_URL` and `BACKEND_URL`

2. **Use HTTPS**:

   - Update Caddyfile with your domain
   - Caddy will automatically get Let's Encrypt certificates

3. **Secure storage**:

   - Use S3 or MinIO with proper access controls
   - Set `STORAGE_TYPE=s3`

4. **Database backups**:

   - Set up regular PostgreSQL backups
   - Use a managed database service (AWS RDS, etc.)

5. **Monitoring**:
   - Add logging and monitoring
   - Set up error tracking (Sentry, etc.)

## 🤝 Support

For issues or questions:

- Check this guide first
- Review the main README.md
- Check the API documentation at `/api/docs`
- Review error logs: `docker compose logs -f`

## 🎉 Congratulations!

You now have a fully functional countdown tracking application! Create your first event and watch the real-time countdown in action.

Happy tracking! ⏱️
