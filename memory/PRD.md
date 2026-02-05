# SchoolCRM - Product Requirements Document

## Original Problem Statement
Build a lightweight CRM system for managing course students and leads. Simple, fast, usable by 5 internal users. Extended with 11 new feature modules.

## Branding
- **System Name:** SchoolCRM (formerly CourseCRM)
- **Logo:** KHAITOV SCHOOL clapperboard icon
- **Color Scheme:** Black & Yellow (primary)

## Architecture
- **Frontend**: React 18 with Tailwind CSS, React Router v6
- **Backend**: FastAPI (Python) with JWT authentication
- **Database**: MongoDB
- **File Storage**: Local (/app/uploads for audio files)
- **Proxy**: React dev server proxy to backend

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
- [ ] **Reminder Push Notifications**: Browser notifications + in-app notification center

### Database Schema
**Collections:**
- `users`: id, name, email, phone, password, role, created_at
- `clients`: id, name, phone, source, manager_id, status, is_lead, is_archived, archived_at, tariff_id, created_at
- `notes`: id, client_id, text, author_id, author_name, created_at
- `payments`: id, client_id, amount, currency, status, date, created_at
- `reminders`: id, client_id, user_id, text, remind_at, is_completed, notified, created_at
- `statuses`: id, name, color, order, is_default, created_at
- `tariffs`: id, name, price, currency, description, created_at
- `settings`: id, key, currency, created_at
- `notifications`: id, user_id, title, message, type, entity_id, is_read, created_at
- `activity_log`: id, user_id, user_name, action, entity_type, entity_id, details, created_at
- `audio_files`: id, client_id, filename, original_name, content_type, size, uploader_id, uploader_name, created_at

## Testing Status
- Phase 1 & 2: 100% pass
- Phase 3 (Completed): 100% pass (iteration_3.json, iteration_4.json)
- Audio Playback Fix: 100% pass (iteration_7.json)

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
- Audio: GET /api/audio/{client_id}, POST /api/audio/upload, GET /api/audio/file/{id}, DELETE /api/audio/{id}
- Export: GET /api/export/clients
- Import: POST /api/import/preview, POST /api/import/save
- Dashboard: GET /api/dashboard/stats, GET /api/dashboard/recent-clients, GET /api/dashboard/recent-notes, GET /api/dashboard/manager-stats, GET /api/dashboard/analytics
- Notifications: GET /api/notifications, GET /api/notifications/unread-count, PUT /api/notifications/{id}/read, PUT /api/notifications/read-all, GET /api/notifications/check-reminders

## Credentials
- Admin: admin@crm.local / admin123
