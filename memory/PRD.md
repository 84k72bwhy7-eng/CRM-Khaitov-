# CourseCRM - Product Requirements Document

## Original Problem Statement
Build a lightweight CRM system for managing course students and leads. Simple, fast, usable by 5 internal users. Core features: authentication, client management, lead status tracking, manager assignment, notes, payment tracking, dashboard, search & filters.

## Architecture
- **Frontend**: React 18 with Tailwind CSS, React Router v6
- **Backend**: FastAPI (Python) with JWT authentication
- **Database**: MongoDB
- **Proxy**: Nginx (routes /api to backend on 8001, frontend on 3000)

## User Personas
1. **Admin**: Full access - manages users, sees all clients, all features
2. **Manager**: Limited access - sees only assigned clients, can add notes/payments

## Core Requirements (Static)
- JWT-based authentication (admin/manager roles)
- Client CRUD with status management (New, Contacted, Sold)
- Manager assignment per client
- Notes system per client
- Payment tracking (paid/pending)
- Dashboard with stats
- Search & filter clients
- Bilingual support (Uzbek/Russian)
- Premium SaaS UI (Black & Yellow branding)

## What's Been Implemented (2026-02-04)
### ✅ Completed Features
- [x] JWT Authentication system with login/logout
- [x] Role-based access control (admin/manager)
- [x] Default admin account (admin@crm.local / admin123)
- [x] Dashboard with stats: today's leads, total clients, sales count, payments
- [x] Client management: add, edit, delete, view details
- [x] Client status management (new, contacted, sold)
- [x] Notes system: add/delete notes per client
- [x] Payment tracking: add payments, view all payments, filter by status
- [x] User management (admin only): add, edit, delete users
- [x] Settings page: update profile, change password
- [x] Search clients by phone/name
- [x] Filter clients by status
- [x] Language switcher (Uzbek/Russian)
- [x] Premium UI with Black sidebar, Yellow accents, White background
- [x] Mobile responsive layout
- [x] All API endpoints with proper error handling

### Database Schema
- **users**: id, name, email, phone, password, role, created_at
- **clients**: id, name, phone, source, manager_id, status, created_at
- **notes**: id, client_id, text, author_id, author_name, created_at
- **payments**: id, client_id, amount, status, date, created_at

## Testing Status
- Backend: 100% pass (23/23 API tests)
- Frontend: 95% pass (all features working)

## Prioritized Backlog

### P0 (Critical) - None remaining
All core MVP features completed

### P1 (High Priority)
- [ ] Bulk client import (CSV upload)
- [ ] Client export to Excel/PDF
- [ ] Manager assignment in client list view
- [ ] Payment history per client with totals

### P2 (Medium Priority)
- [ ] Dashboard charts/graphs
- [ ] Date range filters for clients
- [ ] Email/SMS notifications for managers
- [ ] Activity log for client interactions

### Future Enhancements
- WhatsApp/Telegram integration for lead capture
- Course enrollment tracking
- Automated lead assignment rules
- Report generation and analytics

## Next Tasks
1. Add bulk import feature for clients
2. Implement export functionality
3. Add activity logging
4. Consider notification system for new leads

## Credentials
- Admin: admin@crm.local / admin123
