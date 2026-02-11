# SchoolCRM - Product Requirements Document

## Original Problem Statement
Build a lightweight CRM system for managing course students and leads. Simple, fast, usable by 5 internal users. Extended with 11 new feature modules. Now also accessible as a Telegram Mini App.

## Branding
- **System Name:** SchoolCRM (formerly CourseCRM)
- **Logo:** KHAITOV SCHOOL clapperboard icon
- **Color Scheme:** Black & Yellow (primary)

## Architecture
- **Frontend**: React 18 with Tailwind CSS, React Router v6
- **Backend**: FastAPI (Python) with JWT authentication
- **Database**: Supabase PostgreSQL (migrated from MongoDB on 2026-02-11)
- **File Storage**: Local (/app/uploads for audio files)
- **Proxy**: React dev server proxy to backend
- **Telegram Integration**: Telegram WebApp SDK + Bot API

## Deployment & Environment Protection
- **APP_ENV**: `development` | `staging` | `production`
- **DISABLE_SEED**: Auto-disabled in production
- **Database Protection**: Seeds only run on empty collections in non-production
- **Verification**: `/api/health` and `/api/admin/database-status` endpoints
- **Documentation**: See `/app/DEPLOYMENT.md` for safe deployment guide

## User Personas
1. **Admin**: Full access - manages users, statuses, tariffs, sees all clients, activity log
2. **Manager**: Limited access - sees only assigned clients, can add notes/payments/reminders

## Core Requirements (Static)
- JWT-based authentication (admin/manager roles)
- Client CRUD with status management
- Manager assignment per client
- Notes/Comments system per client
- Payment tracking with USD/UZS currency
- Dashboard with stats
- Search & filter clients
- Bilingual support (Uzbek/Russian)
- Premium SaaS UI (Black & Yellow branding)

## What's Been Implemented

### Phase 1 - MVP (2026-02-04)
- [x] JWT Authentication with login/logout
- [x] Role-based access control
- [x] Dashboard with basic stats
- [x] Client CRUD operations
- [x] Notes system
- [x] Payment tracking
- [x] User management (admin)
- [x] Language switcher (UZ/RU)

### Phase 2 - Extended Features (2026-02-04)
- [x] **Lead Comments**: Notes system enhanced with author, timestamp, sorted newest first
- [x] **USD Currency Support**: Payments stored with currency field, default USD, $ display
- [x] **Reminder System**: Create reminders with date/time, overdue alerts on dashboard, mark complete
- [x] **Custom Status Management**: Admin can add/edit/delete statuses with colors
- [x] **Archive Sold Leads**: Archive/restore functionality with archived view toggle
- [x] **Export All Contacts**: CSV export of clients
- [x] **Activity History / Audit Log**: Track who made changes, what, when (admin only)
- [x] **Manager Sales Statistics**: Dashboard shows per-manager deals and revenue
- [x] **Audio File Upload**: Upload call recordings, play in browser, stored in /app/uploads
- [x] **Full Mobile Optimization**: Responsive UI, hamburger menu, touch-friendly

### Phase 3 - Advanced Features (2026-02-05)
- [x] **Comments & Reminders in Client Creation**: Add initial comment and set reminder when creating a client
- [x] **Tariff Management**: Admin can create/edit/delete course tariffs with price and currency
- [x] **Currency Switcher**: Admin can switch system currency between USD and UZS in settings
- [x] **Excel/CSV Client Import**: Bulk import with preview, duplicate detection, and validation (Admin only)
- [x] **Advanced Dashboard Analytics**: Charts for monthly sales, revenue comparison, growth metrics (Admin only)
- [x] **Edit Payment Function**: Edit existing payments with activity logging (old/new values tracked)
- [x] **Client Group Management**: Admin CRUD for groups, client assignment, filtering by group
- [x] **Sold Client Management**: Dedicated page for sold clients with filtering, archive/restore functionality
- [x] **Audio Playback Fix**: Fixed JWT token validation bug in `/api/audio/stream/{audio_id}` endpoint (2026-02-05)
- [x] **Telegram Mini App Integration**: Backend auth endpoints + Frontend WebApp SDK support (2026-02-11)
- [ ] **Reminder Push Notifications**: Browser notifications + in-app notification center

### Phase 4 - Telegram Integration (2026-02-11)
- [x] **Telegram Auth Backend**: `/api/auth/telegram` endpoint with HMAC-SHA256 validation
- [x] **Account Linking**: `/api/auth/telegram/link` endpoint to link CRM users to Telegram
- [x] **Frontend WebApp SDK**: Auto-detect Telegram context, theme adaptation
- [x] **Dual Auth Support**: Works as both web app (email/password) and Telegram Mini App (auto-login)
- [x] **Bot Setup**: Bot configured as @khaitov_crm_bot
- [x] **Mobile UX Optimization**: Floating add button, quick actions, clickable phones, card layout
- [x] **Telegram Reminder Notifications**: Automatic sending of due reminders via Telegram bot
- [x] **Notification Status UI**: Admin dashboard in Settings showing notification stats
- [x] **Instagram Lead Workflow**: Quick add with Instagram default, success actions (Call/Reminder/Note)
- [x] **Mini App Deep Linking**: Reminder buttons now use `web_app` type to open CRM inside Telegram (2026-02-11)
- [x] **PWA Support for Add to Home Screen**: Full PWA implementation with manifest.json, service worker, and app icons (2026-02-11)

### Phase 5 - Database Migration (2026-02-11)
- [x] **Supabase Migration**: Complete migration from MongoDB to Supabase PostgreSQL
- [x] **Data Migration**: All existing data migrated (users, clients, payments, reminders, notes, statuses, groups, tariffs, settings, activity_log, audio_files)
- [x] **Backend Refactor**: Complete rewrite of server.py to use supabase-py client instead of pymongo
- [x] **UUID IDs**: Switched from MongoDB ObjectIds to PostgreSQL UUIDs
- [x] **Frontend API Hook Fix**: Updated useApi hook to properly include auth headers

### Database Schema (PostgreSQL)
**Tables:**
- `users`: id (uuid), name, email, phone, password, role, telegram_id, telegram_username, telegram_first_name, telegram_linked_at, created_at
- `clients`: id (uuid), mongo_id, name, phone, source, manager_id (fk), status, is_lead, archived, archived_at, tariff_id (fk), group_id (fk), created_at
- `notes`: id (uuid), client_id (fk), user_id (fk), text, created_at
- `payments`: id (uuid), client_id (fk), user_id (fk), amount, currency, status, payment_date, comment, created_at
- `reminders`: id (uuid), client_id (fk), user_id (fk), text, remind_at, is_completed, notified, telegram_sent, telegram_sent_at, telegram_success, created_at
- `statuses`: id (uuid), name, color, sort_order, is_default, created_at
- `tariffs`: id (uuid), name, price, currency, description, created_at
- `groups`: id (uuid), name, color, description, created_at
- `settings`: id (uuid), key, currency, data (jsonb), created_at
- `notifications`: id (uuid), user_id (fk), title, message, type, entity_type, entity_id, is_read, created_at
- `activity_log`: id (uuid), user_id, user_name, action, entity_type, entity_id, details (jsonb), created_at
- `audio_files`: id (uuid), client_id (fk), user_id (fk), filename, original_name, content_type, created_at

## Testing Status
- Phase 1 & 2: 100% pass
- Phase 3 (Completed): 100% pass (iteration_3.json, iteration_4.json)
- Audio Playback Fix: 100% pass (iteration_7.json)
- Supabase Migration: 100% pass (iteration_8.json) - All 33 backend tests + frontend verification passed
- **Frontend Bug Fix (ClientsPage): 100% pass (iteration_9.json)** - Fixed React StrictMode race condition in data loading

## Bug Fixes (2026-02-11)
- **[P0] ClientsPage Rendering Bug**: Fixed critical bug where clients list showed "Loading..." indefinitely
  - **Root Cause**: Race condition in React StrictMode where cleanup function invalidated state updates
  - **Fix**: Implemented proper isMounted pattern for data fetching
  - **File**: `/app/frontend/src/pages/ClientsPage.js`

- **[P1] DashboardPage Analytics Not Loading**: Fixed issue where analytics charts weren't displayed
  - **Root Cause**: Same StrictMode race condition as ClientsPage
  - **Fix**: Separated data loading into two useEffect hooks (basic data + admin-only data)
  - **File**: `/app/frontend/src/pages/DashboardPage.js`

## Prioritized Backlog

### P1 (High Priority) - Phase 3 Remaining
- [ ] **Reminder Push Notifications**: Browser notifications + notification center UI

### P2 (Medium Priority) - Future
- [ ] Email/SMS integration for notifications
- [ ] Client tags/categories
- [ ] Report generation (PDF)

### Future Enhancements
- WhatsApp/Telegram integration for lead capture
- Course enrollment tracking
- Automated lead assignment rules
- Multi-tenant support

## API Endpoints
- Auth: POST /api/auth/login, GET /api/auth/me, PUT /api/auth/profile
- **Telegram Auth**: POST /api/auth/telegram, POST /api/auth/telegram/link
- Users: GET/POST /api/users, PUT/DELETE /api/users/{id}
- Clients: GET/POST /api/clients, GET/PUT/DELETE /api/clients/{id}
- Archive: POST /api/clients/{id}/archive, POST /api/clients/{id}/restore
- Convert: POST /api/clients/{id}/convert-to-lead
- Notes: GET /api/notes/{client_id}, POST /api/notes, DELETE /api/notes/{id}
- Payments: GET /api/payments, GET /api/payments/client/{id}, POST/PUT/DELETE /api/payments/{id}
- Reminders: GET /api/reminders, GET /api/reminders/overdue, POST/PUT/DELETE /api/reminders/{id}
- Statuses: GET/POST /api/statuses, PUT/DELETE /api/statuses/{id}
- Tariffs: GET/POST /api/tariffs, PUT/DELETE /api/tariffs/{id}
- Settings: GET/PUT /api/settings
- Activity: GET /api/activity-log
- Audio: GET /api/audio/{client_id}, POST /api/audio/upload, GET /api/audio/file/{id}, GET /api/audio/stream/{id}?token=..., DELETE /api/audio/{id}
- Export: GET /api/export/clients
- Import: POST /api/import/preview, POST /api/import/save
- Dashboard: GET /api/dashboard/stats, GET /api/dashboard/recent-clients, GET /api/dashboard/recent-notes, GET /api/dashboard/manager-stats, GET /api/dashboard/analytics
- Notifications: GET /api/notifications, GET /api/notifications/unread-count, PUT /api/notifications/{id}/read, PUT /api/notifications/read-all, GET /api/notifications/check-reminders

## Credentials
- Admin: admin@crm.local / admin123
