# Google Cloud Run Deployment Guide

This guide walks you through deploying the BEST Galaxy Assessment application (frontend + backend) to Google Cloud Run.

## Architecture

The application is deployed as **two separate Cloud Run services**:

1. **Backend API** - Python FastAPI server (port 8080)
2. **Frontend** - React app served by Nginx (port 8080)

The frontend proxies API requests to the backend service.

## Prerequisites

### 1. Install Google Cloud SDK

```bash
# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows
# Download from: https://cloud.google.com/sdk/docs/install
```

### 2. Authenticate with Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Create a Google Cloud Project

```bash
# Create new project
gcloud projects create your-project-id --name="BEST Galaxy Assessment"

# Set as active project
gcloud config set project your-project-id

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

### 4. Set Up Secrets in Google Secret Manager

Store sensitive credentials as secrets:

```bash
# Supabase credentials
echo -n "your-supabase-url" | gcloud secrets create SUPABASE_URL --data-file=-
echo -n "your-supabase-key" | gcloud secrets create SUPABASE_KEY --data-file=-

# Stripe credentials
echo -n "your-stripe-secret-key" | gcloud secrets create STRIPE_SECRET_KEY --data-file=-
echo -n "your-stripe-webhook-secret" | gcloud secrets create STRIPE_WEBHOOK_SECRET --data-file=-

# OpenAI API key
echo -n "your-openai-api-key" | gcloud secrets create OPENAI_API_KEY --data-file=-

# Grant Cloud Run access to secrets
PROJECT_NUMBER=$(gcloud projects describe your-project-id --format="value(projectNumber)")
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Deployment Methods

### Option 1: Automated Deployment (Recommended)

Use the provided deployment script:

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"  # or your preferred region

# Run deployment script
./deploy.sh
```

The script will:
- Enable required Google Cloud APIs
- Build and deploy the backend API
- Build and deploy the frontend
- Configure environment variables and secrets
- Display the deployed URLs

### Option 2: Manual Deployment

#### Deploy Backend

```bash
# From project root
gcloud run deploy best-galaxy-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "ENVIRONMENT=production" \
    --set-secrets "SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest,STRIPE_SECRET_KEY=STRIPE_SECRET_KEY:latest,STRIPE_WEBHOOK_SECRET=STRIPE_WEBHOOK_SECRET:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest"

# Get backend URL
BACKEND_URL=$(gcloud run services describe best-galaxy-backend \
    --region us-central1 \
    --format 'value(status.url)')

echo "Backend URL: $BACKEND_URL"
```

#### Deploy Frontend

```bash
# From frontend directory
cd frontend

gcloud run deploy best-galaxy-frontend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --timeout 60 \
    --set-env-vars "BACKEND_URL=$BACKEND_URL"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe best-galaxy-frontend \
    --region us-central1 \
    --format 'value(status.url)')

echo "Frontend URL: $FRONTEND_URL"
```

## Post-Deployment Configuration

### 1. Update Stripe Webhook

Update your Stripe webhook endpoint to point to the deployed backend:

```
Webhook URL: https://your-backend-url.run.app/api/v1/payment/webhook
```

Go to: https://dashboard.stripe.com/webhooks

### 2. Update CORS Settings (if needed)

If you encounter CORS issues, update the backend CORS configuration in `scoring_engine/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-url.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Configure Custom Domain (Optional)

```bash
# Map custom domain to frontend
gcloud run services update best-galaxy-frontend \
    --region us-central1 \
    --add-cloudsql-instances your-domain.com

# Map custom domain to backend API
gcloud run services update best-galaxy-backend \
    --region us-central1 \
    --add-cloudsql-instances api.your-domain.com
```

## Monitoring and Logs

### View Logs

```bash
# Backend logs
gcloud run services logs tail best-galaxy-backend --region us-central1

# Frontend logs
gcloud run services logs tail best-galaxy-frontend --region us-central1

# Follow logs in real-time
gcloud run services logs tail best-galaxy-backend --region us-central1 --follow
```

### View Metrics

```bash
# Open Cloud Console
gcloud run services describe best-galaxy-backend --region us-central1

# Or visit: https://console.cloud.google.com/run
```

## Updating the Application

### Update Backend

```bash
# Make your code changes, then redeploy
gcloud run deploy best-galaxy-backend \
    --source . \
    --region us-central1
```

### Update Frontend

```bash
cd frontend
gcloud run deploy best-galaxy-frontend \
    --source . \
    --region us-central1
```

## Environment Variables

### Backend Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon/service key | Yes |
| `STRIPE_SECRET_KEY` | Stripe secret key | Yes |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes |
| `ENVIRONMENT` | Set to `production` | No |

### Frontend Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BACKEND_URL` | Backend API URL | Yes |

## Cost Optimization

Cloud Run pricing is based on:
- **CPU and Memory**: Only charged when handling requests
- **Requests**: $0.40 per million requests
- **Networking**: Egress charges apply

### Tips to Reduce Costs

1. **Set minimum instances to 0** (default in our config)
2. **Use appropriate memory allocation**:
   - Backend: 1Gi (can reduce to 512Mi if needed)
   - Frontend: 512Mi
3. **Set request timeout** to avoid long-running requests
4. **Enable Cloud CDN** for static assets (frontend)

## Troubleshooting

### Build Fails

```bash
# Check build logs
gcloud builds list --limit 5
gcloud builds log <BUILD_ID>
```

### Service Not Responding

```bash
# Check service status
gcloud run services describe best-galaxy-backend --region us-central1

# Check recent logs
gcloud run services logs read best-galaxy-backend --region us-central1 --limit 50
```

### Database Connection Issues

Ensure Supabase secrets are correctly set:

```bash
# Verify secrets exist
gcloud secrets list

# Update secret if needed
echo -n "new-value" | gcloud secrets versions add SUPABASE_URL --data-file=-
```

### Frontend Can't Reach Backend

1. Check `BACKEND_URL` environment variable is set correctly
2. Verify backend service is deployed and running
3. Check nginx.conf proxy configuration

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use Secret Manager** for all sensitive data
3. **Enable Cloud Armor** for DDoS protection (optional)
4. **Set up Cloud IAM** roles properly
5. **Enable audit logging** for compliance

## Rollback

If deployment fails or has issues:

```bash
# List revisions
gcloud run revisions list --service best-galaxy-backend --region us-central1

# Rollback to previous revision
gcloud run services update-traffic best-galaxy-backend \
    --to-revisions REVISION_NAME=100 \
    --region us-central1
```

## Support

For issues:
1. Check logs first: `gcloud run services logs tail <service-name>`
2. Verify environment variables and secrets
3. Test locally with Docker before deploying
4. Check Cloud Run quotas and limits

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
