# SchoolCRM Deployment Guide

## ⚠️ CRITICAL: Database Protection

**PROBLEM SOLVED:** Production database was being overwritten because:
1. Development and production used the same database configuration
2. Seed scripts ran on every deployment, inserting demo data
3. No environment separation existed

**SOLUTION IMPLEMENTED:**
- Environment-based configuration (`APP_ENV=production`)
- Automatic seed disabling in production (`DISABLE_SEED=true`)
- Separate database names for dev/staging/production

---

## Environment Configuration

### Development (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=crm_db
APP_ENV=development
DISABLE_SEED=false
```

### Staging (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=crm_staging
APP_ENV=staging
DISABLE_SEED=false
```

### Production (.env)
```env
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net
DB_NAME=schoolcrm_production
APP_ENV=production
DISABLE_SEED=true
```

---

## Safe Deployment Workflow

### Step 1: Pre-Deployment Checklist
- [ ] Backup production database
- [ ] Verify `.env` has `APP_ENV=production`
- [ ] Verify `.env` has `DISABLE_SEED=true`
- [ ] Verify `DB_NAME` is production database name
- [ ] Verify `MONGO_URL` points to production MongoDB

### Step 2: Deploy Code
```bash
# Code deployment only updates application files
# Database is NOT touched during deployment
```

### Step 3: Post-Deployment Verification
```bash
# Check health endpoint
curl https://your-domain.com/api/health

# Expected response:
{
  "status": "healthy",
  "environment": "production",
  "database": "schoolcrm_production",
  "seed_disabled": true
}
```

### Step 4: Admin Verification
Login as admin and check:
```
GET /api/admin/database-status
```

Expected:
- `is_production: true`
- `seed_disabled: true`
- `protection_status: "ENABLED"`
- Client count should match your data

---

## Protection Mechanisms

### 1. Environment Detection
```python
APP_ENV = os.environ.get("APP_ENV", "development")
IS_PRODUCTION = APP_ENV == "production"
```

### 2. Seed Disabling
```python
DISABLE_SEED = IS_PRODUCTION or os.environ.get("DISABLE_SEED") == "true"

if DISABLE_SEED:
    print("[App] PRODUCTION MODE - All seeding disabled")
```

### 3. Conditional Seeding
Seeds only run when:
- `APP_ENV != production`
- `DISABLE_SEED != true`
- No existing data in the collection

### 4. Data Check Before Insert
```python
# Only creates admin if NO users exist
if users_collection.count_documents({}) == 0:
    # Create admin
```

---

## Rollback Procedure (If Data Lost)

### Immediate Steps:
1. **Stop the server** to prevent further changes
2. **Check backup** - Restore from latest backup
3. **Verify .env** - Ensure production settings are correct

### MongoDB Restore:
```bash
# From MongoDB Atlas
mongorestore --uri="mongodb+srv://..." /path/to/backup

# From mongodump
mongorestore --db schoolcrm_production /path/to/dump/schoolcrm_production
```

---

## Database Backup Best Practices

### Daily Automated Backups
1. Use MongoDB Atlas automated backups
2. Or set up cron job:
```bash
0 2 * * * mongodump --uri="$MONGO_URL" --out /backups/$(date +%Y%m%d)
```

### Before Each Deployment
```bash
mongodump --uri="$MONGO_URL" --out /backups/pre-deploy-$(date +%Y%m%d-%H%M)
```

---

## Environment Variables Reference

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `APP_ENV` | development | **production** | Environment mode |
| `DISABLE_SEED` | false | **true** | Disables all data seeding |
| `DB_NAME` | crm_db | schoolcrm_production | Database name |
| `MONGO_URL` | localhost | Cloud MongoDB | Database connection |
| `JWT_SECRET` | dev-secret | **unique-secret** | Auth token secret |

---

## Verification Endpoints

### Health Check (Public)
```
GET /api/health
```

### Database Status (Admin Only)
```
GET /api/admin/database-status
Authorization: Bearer <admin-token>
```

---

## Contact for Issues

If production data is lost:
1. Immediately stop deployments
2. Check backup availability
3. Review deployment logs
4. Verify environment configuration
