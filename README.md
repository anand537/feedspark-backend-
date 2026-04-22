# Auto Feedback Backend

> **Latest Update:** ✅ Database migrated to **Supabase PostgreSQL** (Cloud-based)
> See [SUPABASE_QUICK_START.md](SUPABASE_QUICK_START.md) for migration details.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Pip package manager
- Supabase account (free tier available)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   # Copy template
   cp .env.example .env
   
   # Edit .env with your Supabase credentials:
   DATABASE_URL=postgresql+psycopg2://user:password@host:5432/postgres
   JWT_SECRET_KEY=your-secret-key
   OPENAI_API_KEY=your-openai-key
   ```

3. **Verify setup:**
   ```bash
   python test_supabase_connection.py
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```
   Application will start at `http://localhost:5000`

## 🧪 Testing

### Test Database Connection
```bash
python test_supabase_connection.py
```

### Run Authentication Tests
```bash
python test_auth_manual.py
```
All 10 tests should pass ✓

### Manual API Testing
Import `postman_collection.json` into Postman for interactive API testing.

## 📝 API Example

```bash
# Generate feedback for a student
curl -X POST http://127.0.0.1:5000/generate-feedback \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Priya Sharma",
    "communication": 8,
    "teamwork": 7,
    "creativity": 9,
    "critical_thinking": 6,
    "presentation": 8
  }'
```

## 🗄️ Database

The application now uses **Supabase PostgreSQL** (cloud-based):
- ✅ Automatic backups
- ✅ Multi-user access
- ✅ Enterprise features
- ✅ SSL/TLS encryption
- ✅ Scalable infrastructure

**Before:** SQLite (local file)
**After:** PostgreSQL (cloud-hosted)

See [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) for technical details.

## 📚 Documentation

- [SUPABASE_QUICK_START.md](SUPABASE_QUICK_START.md) - Quick setup guide
- [SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md) - Complete migration guide
- [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md) - Authentication system details
- [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) - Comprehensive migration summary

## 🔧 Development

### Project Structure
```
app/
├── __init__.py          # Flask app factory
├── extensions.py        # SQLAlchemy, JWT, Mail setup
├── ai.py               # AI/OpenAI integration
├── email_utils.py      # Email utilities
├── decorators.py       # Custom decorators
├── models/             # SQLAlchemy models
├── routes/             # Flask blueprints
├── api/                # API endpoints
└── static/             # Frontend files
```

### Environment Variables
```
DATABASE_URL=postgresql+psycopg2://...  # Supabase connection
JWT_SECRET_KEY=...                      # JWT signing key
OPENAI_API_KEY=...                      # OpenAI API key
FLASK_ENV=development                   # Environment
FLASK_DEBUG=true                        # Debug mode
SQLALCHEMY_ECHO=false                   # SQL logging
```

## 🚢 Deployment

### Production Setup
1. Set strong `JWT_SECRET_KEY`
2. Set `FLASK_ENV=production`
3. Set `FLASK_DEBUG=false`
4. Configure production Supabase database
5. Deploy to your chosen platform (Heroku, AWS, Railway, etc.)

See [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md#-deployment-guide) for detailed deployment instructions.

## 🐛 Troubleshooting

**Issue:** Database connection error
- **Solution:** Check .env file has correct DATABASE_URL

**Issue:** Tests failing
- **Solution:** Run `python test_supabase_connection.py` to diagnose

**Issue:** Module not found errors
- **Solution:** Run `pip install -r requirements.txt`

See [SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md#troubleshooting) for more troubleshooting.

## 📞 Support

- **Team Documentation:** See markdown files in project root
- **Supabase Docs:** https://supabase.com/docs
- **Flask Docs:** https://flask.palletsprojects.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
