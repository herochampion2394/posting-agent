# Posting Agent - Deployment Guide

## Required GitHub Secrets

Go to: https://github.com/herochampion2394/posting-agent/settings/secrets/actions

Add these secrets:

### Google Cloud Platform
- `GCP_PROJECT_ID` - Your GCP project ID
- `GCP_SA_KEY` - Service account JSON key (entire file contents)
- `GCP_REGION` - `asia-east1` (or your preferred region)

### Database
- `DATABASE_URL` - `postgresql://postgres:Been1chu1@3@35.229.232.204:5432/posting_agent`

### Backend Security
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`

### OpenAI
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys

### Twitter API (from developer.twitter.com)
- `TWITTER_API_KEY` - Your Consumer Key
- `TWITTER_API_SECRET` - Your Consumer Secret
- `TWITTER_CALLBACK_URL` - `https://your-frontend-url.run.app/auth/twitter/callback`

### TikTok API (from developers.tiktok.com)
- `TIKTOK_CLIENT_KEY` - Your Client Key
- `TIKTOK_CLIENT_SECRET` - Your Client Secret
- `TIKTOK_REDIRECT_URI` - `https://your-frontend-url.run.app/auth/tiktok/callback`

### Frontend
- `VITE_API_URL` - `https://posting-agent-backend-xxx.run.app` (update after backend deploys)

## Setup Steps

### 1. Create PostgreSQL Database

Connect to your PostgreSQL server:
```bash
psql -h 35.229.232.204 -U postgres -d postgres
```

Create database:
```sql
CREATE DATABASE posting_agent;
```

### 2. Set Up Google Cloud

Create Artifact Registry repository:
```bash
gcloud artifacts repositories create posting-agent \
  --repository-format=docker \
  --location=asia-east1
```

Create service account:
```bash
gcloud iam service-accounts create posting-agent-deploy

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:posting-agent-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:posting-agent-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud iam service-accounts keys create key.json \
  --iam-account=posting-agent-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

Copy contents of `key.json` as `GCP_SA_KEY` secret.

### 3. Get API Keys

**OpenAI**: https://platform.openai.com/api-keys

**Twitter**:
1. Apply at https://developer.twitter.com/
2. Create app, enable OAuth 1.0a
3. Get API Key and Secret

**TikTok**:
1. Apply at https://developers.tiktok.com/
2. Create app, request Content Posting API access
3. Get Client Key and Secret

### 4. Deploy

```bash
git push origin main
```

GitHub Actions will automatically deploy.

Get URLs:
```bash
gcloud run services describe posting-agent-backend --region=asia-east1 --format="value(status.url)"
gcloud run services describe posting-agent-frontend --region=asia-east1 --format="value(status.url)"
```

### 5. Update Callback URLs

After deployment:
1. Update `TWITTER_CALLBACK_URL` and `TIKTOK_REDIRECT_URI` secrets with actual frontend URL
2. Update `VITE_API_URL` secret with backend URL
3. Update callback URLs in Twitter and TikTok developer portals
4. Re-deploy by pushing a commit

## Monitoring

```bash
# View logs
gcloud run logs read posting-agent-backend --region=asia-east1 --limit=50

# Check service status
gcloud run services list
```
