# Quick Start: Deploy to Google Cloud Run

This is a simplified guide to get your application deployed quickly.

## 1. Prerequisites (5 minutes)

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Login
gcloud auth login
```

## 2. Create Project & Enable APIs (2 minutes)

```bash
# Set your project ID
export PROJECT_ID="best-galaxy-$(date +%s)"

# Create project
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable billing at: https://console.cloud.google.com/billing

# Enable APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com
```

## 3. Store Secrets (3 minutes)

```bash
# Supabase
echo -n "YOUR_SUPABASE_URL" | gcloud secrets create SUPABASE_URL --data-file=-
echo -n "YOUR_SUPABASE_KEY" | gcloud secrets create SUPABASE_KEY --data-file=-

# Stripe
echo -n "YOUR_STRIPE_SECRET_KEY" | gcloud secrets create STRIPE_SECRET_KEY --data-file=-
echo -n "YOUR_STRIPE_WEBHOOK_SECRET" | gcloud secrets create STRIPE_WEBHOOK_SECRET --data-file=-

# OpenAI
echo -n "YOUR_OPENAI_API_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=-

# Grant access
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## 4. Deploy (5 minutes)

```bash
# Set environment variables
export GCP_PROJECT_ID=$PROJECT_ID
export GCP_REGION="us-central1"

# Run deployment script
./deploy.sh
```

That's it! The script will output your application URLs.

## 5. Post-Deployment (2 minutes)

1. **Update Stripe webhook**: Copy the backend URL and add `/api/v1/payment/webhook`
   - Go to: https://dashboard.stripe.com/webhooks
   - Add endpoint: `https://your-backend-url.run.app/api/v1/payment/webhook`

2. **Test your app**: Visit the frontend URL provided by the deployment script

## Troubleshooting

**Build fails?**
```bash
gcloud builds list --limit 5
gcloud builds log <BUILD_ID>
```

**Service not working?**
```bash
# Check logs
gcloud run services logs tail best-galaxy-backend --region us-central1 --follow
```

**Need to update?**
```bash
# Just run deploy.sh again
./deploy.sh
```

## Costs

- **Free tier**: 2 million requests/month, 360,000 GB-seconds/month
- **Typical cost**: $5-20/month for small to medium traffic
- **Auto-scaling**: Scales to zero when not in use (no cost)

## Next Steps

See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Custom domains
- Advanced configuration
- Monitoring and alerts
- Security best practices
