# 🔒 Security Configuration Guide

## CRITICAL: Protecting Your Credentials

This guide ensures all sensitive credentials and API keys are properly protected and never committed to version control.

---

## 1. Environment Variables Setup

### What Should Be in `.env`?

Your `.env` file should ONLY contain:
- Database connection strings
- API keys
- JWT secrets
- Environment-specific settings

### What Should NEVER Be in Code?

❌ **NEVER hardcode:**
- API keys
- Database passwords
- Secret keys
- Personal information
- Internal URLs/IPs

---

## 2. Creating Your Local `.env` File

### Step 1: Copy the Template
```bash
cp backend/.env.example backend/.env
```

### Step 2: Edit with Real Values
```bash
nano backend/.env
# or use your preferred editor
```

### Step 3: Add Your Real Credentials
```
# DATABASE
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_REAL_PASSWORD@your-host:5432/core_inventory

# AUTHENTICATION
JWT_SECRET_KEY=generate-a-long-random-string-here

# AI SERVICES
GROQ_API_KEY=gsk_your_real_groq_api_key_here

# ENVIRONMENT
ENVIRONMENT=development
```

---

## 3. Credential Generation

### Generate Strong JWT Secret
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Get Groq API Key
1. Visit https://console.groq.com
2. Sign up / Log in
3. Generate new API key
4. Copy and paste into `.env`

### Database Password
Use a strong password with:
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words

---

## 4. File Protection (`.gitignore`)

The `.gitignore` file in `backend/` ensures `.env` is never committed:

```
# Environment Variables
.env
.env.local
.env.*.local
```

### Verify `.env` is Ignored
```bash
git status
# Should NOT show backend/.env in changes
```

---

## 5. What Gets Committed vs. Ignored

### ✅ Committed to Repository
- `.env.example` (placeholder values only)
- Configuration code (config.py)
- Source code
- Documentation

### ❌ NEVER Committed
- `.env` (your real credentials)
- API keys
- Passwords
- Private keys
- Secrets

---

## 6. Config.py Pattern (How Credentials Are Used)

The `config.py` file demonstrates the proper pattern:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str              # Read from .env
    JWT_SECRET_KEY: str            # Read from .env
    GROQ_API_KEY: str = ""         # Read from .env
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"          # Load from .env file

settings = Settings()  # Access: settings.DATABASE_URL, settings.JWT_SECRET_KEY, etc.
```

### Usage in Code
```python
# In client.py
from config import settings

client = Groq(api_key=settings.GROQ_API_KEY)  # ✅ Correct: from env

# NOT like this:
# client = Groq(api_key="gsk_...")  # ❌ NEVER hardcode!
```

---

## 7. Multiple Environment Files

For different environments (dev, staging, prod):

```
backend/
├── .env                 (local development - ignored by git)
├── .env.example         (template - committed to git)
├── .env.staging         (staging - ignored by git)
└── .env.production      (production - ignored by git, deployed separately)
```

To use different env files:
```bash
# Load staging environment
export ENV_FILE=.env.staging
python main.py

# Or in Python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
```

---

## 8. Docker Secrets (Production)

For production deployment with Docker:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend .

# Don't include .env in image
# Pass secrets via environment at runtime
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

```bash
# Pass secrets at runtime
docker run \
  -e DATABASE_URL="postgresql://..." \
  -e JWT_SECRET_KEY="..." \
  -e GROQ_API_KEY="..." \
  -p 8000:8000 \
  core-inventory:latest
```

---

## 9. Secrets Management (Production Best Practices)

For production environments, use dedicated secret management:

### Option 1: AWS Secrets Manager
```python
import boto3

secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='core-inventory/db')
database_url = secret['SecretString']
```

### Option 2: HashiCorp Vault
```python
import hvac

client = hvac.Client(url='http://127.0.0.1:8200', token='your-token')
secret = client.secrets.kv.read_secret_version(path='core-inventory')
database_url = secret['data']['data']['database_url']
```

### Option 3: Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: core-inventory-secrets
type: Opaque
stringData:
  database_url: "postgresql://..."
  jwt_secret_key: "..."
  groq_api_key: "..."
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: core-inventory-api
spec:
  template:
    spec:
      containers:
      - name: api
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: core-inventory-secrets
              key: database_url
```

---

## 10. If Credentials Were Exposed

### Immediate Actions:

1. **Rotate All Credentials**
   ```bash
   # Generate new Groq API key
   # https://console.groq.com → regenerate

   # Generate new JWT secret
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Reset database password
   ALTER USER postgres WITH PASSWORD 'new_password';
   ```

2. **Check Commit History**
   ```bash
   # Search git history for exposed keys
   git log -p --all -S "gsk_" -- "*.py" "*.md"
   git log -p --all -S "DATABASE_URL=" -- "*.py" "*.md"
   ```

3. **Remove from History (Only if Absolutely Necessary)**
   ```bash
   # WARNING: This rewrites history!
   # Only do this for critical exposures
   git filter-branch --tree-filter 'sed -i "s/gsk_[^[:space:]]*//g" .env.example' HEAD

   # Or use BFG (easier):
   bfg --replace-text secrets.txt  # secrets.txt contains patterns to remove
   ```

4. **Force Push**
   ```bash
   # Only on personal repos, not team repos
   git push origin --force --all
   ```

5. **Notify Team**
   - Alert anyone with access to the repo
   - Inform cloud providers if used externally
   - Plan credential rotation schedule

---

## 11. Checking for Exposed Credentials

### Local Check
```bash
# Install git-secrets
brew install git-secrets

# Configure patterns
git secrets --add 'gsk_[A-Za-z0-9_-]+'
git secrets --add 'GROQ_API_KEY'

# Scan repository
git secrets --scan
```

### GitHub Security
- GitHub automatically scans for exposed keys
- Check Settings → Security & analysis → Secret scanning
- GitHub will notify if keys are found

---

## 12. CI/CD Pipeline Security

### GitHub Actions Example
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # ✅ Load secrets from GitHub Secrets, not from .env
      - name: Run tests
        env:
          DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          JWT_SECRET_KEY: ${{ secrets.JWT_SECRET_KEY }}
        run: |
          pip install -r requirements.txt
          pytest
```

### Never Do This:
```yaml
# ❌ WRONG - credentials in code
- name: Set credentials
  run: echo "DATABASE_URL=postgresql://user:password@..." >> .env
```

---

## 13. Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] `.env.example` contains placeholder values only
- [ ] All empty strings or placeholders like "your-api-key-here"
- [ ] No real credentials in any `.py` files
- [ ] config.py reads from environment via BaseSettings
- [ ] All API clients use `settings.VARIABLE_NAME`
- [ ] `.gitignore` checked with `git check-ignore .env`
- [ ] Recent commits don't contain credentials
- [ ] Team members have instructions to create local `.env`
- [ ] Production uses Secrets Manager or equivalent

---

## 14. Team Onboarding

Provide new team members with:

1. **Copy of `.env.example`**
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Instructions to fill values**
   - Where to get database credentials
   - How to generate/get API keys
   - Which environment variables are required

3. **Never commit `.env`**
   ```bash
   # Verify it's ignored
   git status  # should NOT show .env
   ```

4. **How to run locally**
   ```bash
   cd backend
   pip install -r requirements.txt
   python push_csv_file.py  # Uses .env
   uvicorn main:app --reload  # Uses .env
   ```

---

## 15. Quick Reference

| ✅ Commit to Git | ❌ Never Commit to Git |
|-----------------|----------------------|
| `.env.example` with placeholders | `.env` with real values |
| Configuration code | API keys |
| Documentation | Passwords |
| Source code | Secrets |
| `.gitignore` rules | Private credentials |

---

## Support & Questions

If you have questions about secure credential management:
1. Review this guide again
2. Check GitHub's security documentation
3. Consult your security team
4. Never commit sensitive data

---

**Remember:** Better to be over-cautious with security than sorry later! 🔒
