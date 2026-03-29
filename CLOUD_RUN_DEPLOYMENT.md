# Google Cloud Run Deployment Guide

This guide explains how to deploy the BEST Galaxy Assessment project to Google Cloud Run using the "Connect Repository" feature.

## Architecture

- **Backend Service**: Python FastAPI on Cloud Run (Port 8080)
- **Frontend Service**: React app with Nginx on Cloud Run (Port 8080)
- **Database**: Supabase (external)
- **Payments**: Stripe (external)

## Prerequisites

1. Google Cloud Platform account
2. GitHub repository with your code
3. Supabase project with tables created
4. Stripe account with API keys
5. OpenAI API key

## Deployment Steps

### 1. Prepare Your Repository

Ensure these files are in your repository:
- `Dockerfile` (backend)
- `frontend/Dockerfile` (frontend)
- `frontend/nginx.conf` (nginx config)
- `cloudbuild.yaml` (build configuration)
- `.dockerignore` files

### 2. Set Up Google Cloud Project

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. Deploy Backend Using Cloud Console

**Option A: Using "Connect Repository" (Recommended)**

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click **"Create Service"**
3. Select **"Continuously deploy from a repository"**
4. Click **"Set up with Cloud Build"**
5. Connect your GitHub repository
6. Select **Branch**: `main` (or your default branch)
7. **Build Configuration**:
   - Build Type: **Dockerfile**
   - Source location: `/Dockerfile`
8. Click **"Save"**
9. Configure service:
   - **Service name**: `best-galaxy-backend`
   - **Region**: `us-central1` (or your preferred region)
   - **Authentication**: Allow unauthenticated invocations
   - **CPU allocation**: CPU is only allocated during request processing
   - **Memory**: 512 MiB
   - **Maximum instances**: 10
   - **Timeout**: 300 seconds
10. **Environment Variables** (click "Variables & Secrets"):
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   OPENAI_API_KEY=sk-xxxxx
   STRIPE_SECRET_KEY=sk_test_xxxxx
   STRIPE_WEBHOOK_SECRET=whsec_xxxxx
   PORT=8080
   ```
11. Click **"Create"**

**Option B: Using gcloud CLI**

```bash
# Deploy backend
gcloud run deploy best-galaxy-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars SUPABASE_URL=https://xxxxx.supabase.co \
  --set-env-vars SUPABASE_KEY=your-key \
  --set-env-vars OPENAI_API_KEY=sk-xxxxx \
  --set-env-vars STRIPE_SECRET_KEY=sk_test_xxxxx \
  --set-env-vars STRIPE_WEBHOOK_SECRET=whsec_xxxxx \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --timeout 300
```

### 4. Deploy Frontend

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click **"Create Service"**
3. Select **"Continuously deploy from a repository"**
4. Connect same repository
5. **Build Configuration**:
   - Build Type: **Dockerfile**
   - Source location: `/frontend/Dockerfile`
6. Configure service:
   - **Service name**: `best-galaxy-frontend`
   - **Region**: Same as backend
   - **Authentication**: Allow unauthenticated invocations
   - **Memory**: 256 MiB
7. **Environment Variables**:
   ```
   BACKEND_URL=https://best-galaxy-backend-xxxxx.run.app
   ```
   (Replace with your actual backend URL from step 3)
8. Click **"Create"**

### 5. Configure Stripe Webhook

1. Get your backend URL: `https://best-galaxy-backend-xxxxx.run.app`
2. Go to [Stripe Dashboard](https://dashboard.stripe.com/webhooks)
3. Click **"Add endpoint"**
4. Endpoint URL: `https://best-galaxy-backend-xxxxx.run.app/api/v1/payment/webhook`
5. Events to send:
   - `checkout.session.completed`
6. Copy the **Signing secret** (starts with `whsec_`)
7. Update backend environment variable `STRIPE_WEBHOOK_SECRET`

### 6. Update Frontend Environment

Update the frontend's `BACKEND_URL` environment variable:

```bash
gcloud run services update best-galaxy-frontend \
  --region us-central1 \
  --set-env-vars BACKEND_URL=https://best-galaxy-backend-xxxxx.run.app
```

### 7. Test Your Deployment

1. Visit your frontend URL: `https://best-galaxy-frontend-xxxxx.run.app`
2. Test signup/login
3. Complete an assessment
4. Test payment flow
5. Check "My Reports"

## Automated Deployment with Cloud Build

The `cloudbuild.yaml` file enables automatic deployment on every push to your repository.

### Set Up Cloud Build Trigger

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click **"Create Trigger"**
3. Configure:
   - **Name**: `deploy-best-galaxy`
   - **Event**: Push to a branch
   - **Source**: Your repository
   - **Branch**: `^main$`
   - **Configuration**: Cloud Build configuration file
   - **Location**: `cloudbuild.yaml`
4. **Substitution variables** (add these):
   ```
   _SUPABASE_URL: https://xxxxx.supabase.co
   _SUPABASE_KEY: your-supabase-anon-key
   _OPENAI_API_KEY: sk-xxxxx
   _STRIPE_SECRET_KEY: sk_test_xxxxx
   _STRIPE_WEBHOOK_SECRET: whsec_xxxxx
   _BACKEND_URL: https://best-galaxy-backend-xxxxx.run.app
   ```
5. Click **"Create"**

Now every push to `main` will automatically build and deploy both services!

## Environment Variables Reference

### Backend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxxxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon/public key | `eyJhbGc...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-xxxxx` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_test_xxxxx` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_xxxxx` |
| `PORT` | Port to listen on | `8080` |

### Frontend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `BACKEND_URL` | Backend API URL | `https://best-galaxy-backend-xxxxx.run.app` |

## Custom Domain (Optional)

### Map Custom Domain to Services

1. Go to Cloud Run service
2. Click **"Manage Custom Domains"**
3. Add your domain (e.g., `api.yourdomain.com` for backend)
4. Follow DNS configuration instructions
5. Repeat for frontend (e.g., `app.yourdomain.com`)

## Monitoring & Logs

### View Logs

```bash
# Backend logs
gcloud run services logs read best-galaxy-backend --region us-central1

# Frontend logs
gcloud run services logs read best-galaxy-frontend --region us-central1
```

### Monitoring Dashboard

- Go to [Cloud Run Console](https://console.cloud.google.com/run)
- Click on your service
- View metrics: requests, latency, errors, CPU, memory

## Cost Optimization

Cloud Run pricing:
- **Free tier**: 2 million requests/month
- **Pricing**: Pay only for what you use
- **Idle**: No charges when not serving requests

Recommendations:
- Set `--max-instances` to control costs
- Use `--cpu-throttling` for CPU allocation
- Monitor usage in Cloud Console

## Troubleshooting

### Backend won't start
- Check logs: `gcloud run services logs read best-galaxy-backend`
- Verify environment variables are set
- Ensure Supabase tables exist

### Frontend can't reach backend
- Verify `BACKEND_URL` is correct
- Check CORS settings in backend
- Test backend URL directly

### Payment webhook not working
- Verify webhook URL in Stripe dashboard
- Check `STRIPE_WEBHOOK_SECRET` matches
- Review backend logs for webhook errors

### Database connection issues
- Verify `SUPABASE_URL` and `SUPABASE_KEY`
- Check Supabase RLS policies
- Ensure tables exist

## Security Best Practices

1. **Use Secret Manager** for sensitive values:
   ```bash
   echo -n "your-secret" | gcloud secrets create stripe-key --data-file=-
   ```

2. **Enable VPC Connector** for private database access

3. **Set up Cloud Armor** for DDoS protection

4. **Enable Cloud CDN** for frontend static assets

5. **Use Identity-Aware Proxy** for admin endpoints

## Rollback

If deployment fails:

```bash
# List revisions
gcloud run revisions list --service best-galaxy-backend

# Rollback to previous revision
gcloud run services update-traffic best-galaxy-backend \
  --to-revisions REVISION_NAME=100
```

## Support

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Troubleshooting Guide](https://cloud.google.com/run/docs/troubleshooting)
