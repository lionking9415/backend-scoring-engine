# Deploy Frontend to Google Cloud Run - Console Guide

Complete step-by-step guide for deploying the React frontend to Google Cloud Run using the **Google Cloud Console web UI**.

---

## Prerequisites

- ✅ Frontend Docker image built: `best-galaxy-frontend:latest`
- ✅ Backend already deployed to Cloud Run
- ✅ Google Cloud account with access to project `eighth-etching-491401-e5`

---

## Part 1: Push Frontend Image to Artifact Registry

**Note:** You must use command line to push the Docker image. The Console doesn't support direct image uploads.

### Step 1: Authenticate and Configure (One-time setup)

Open your terminal and run:

```bash
export PATH="/tmp/google-cloud-sdk/bin:$PATH"

# Authenticate (if not already done)
gcloud auth login

# Set project
gcloud config set project eighth-etching-491401-e5

# Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Step 2: Tag the Frontend Image

```bash
sudo docker tag best-galaxy-frontend:latest \
  us-central1-docker.pkg.dev/eighth-etching-491401-e5/best-galaxy-backend/frontend:latest
```

**Note:** We're using the `best-galaxy-backend` repository since you don't have permission to create a new repository.

### Step 3: Push to Artifact Registry

```bash
sudo docker push us-central1-docker.pkg.dev/eighth-etching-491401-e5/best-galaxy-backend/frontend:latest
```

This will take 2-5 minutes depending on your internet speed.

### Step 4: Verify Image Upload

1. Go to https://console.cloud.google.com/artifacts
2. Select project: `eighth-etching-491401-e5`
3. Click on `best-galaxy-backend` repository
4. You should see both `backend` and `frontend` images

---

## Part 2: Deploy Frontend to Cloud Run via Console

### Step 1: Get Backend URL

Before deploying frontend, you need the backend URL:

1. Go to https://console.cloud.google.com/run
2. Find `best-galaxy-backend` service
3. Copy the URL (e.g., `https://best-galaxy-backend-xxxxx-uc.a.run.app`)
4. **Save this URL** - you'll need it in Step 6

### Step 2: Open Cloud Run Console

1. Go to https://console.cloud.google.com/run
2. Make sure project `eighth-etching-491401-e5` is selected (top left)
3. Click **"+ CREATE SERVICE"** button

### Step 3: Select Container Image

**Container image URL:**

1. Click **"SELECT"** next to "Container image URL"
2. In the dialog:
   - Click **"Artifact Registry"** tab
   - **Location:** `us-central1`
   - **Repository:** `best-galaxy-backend`
   - **Image:** `frontend`
   - **Tag:** `latest`
3. Click **"SELECT"**

The full image path should be:
```
us-central1-docker.pkg.dev/eighth-etching-491401-e5/best-galaxy-backend/frontend:latest
```

### Step 4: Configure Service Settings

**Service name:**
- Enter: `best-galaxy-frontend`

**Region:**
- Select: `us-central1 (Iowa)`

**CPU allocation and pricing:**
- Select: **"CPU is only allocated during request processing"**

**Autoscaling:**
- **Minimum number of instances:** `0`
- **Maximum number of instances:** `5`

**Ingress:**
- Select: **"Allow all traffic"**

**Authentication:**
- Select: **"Allow unauthenticated invocations"** ✓

### Step 5: Configure Container Settings

Click **"CONTAINER, VARIABLES & SECRETS, CONNECTIONS, SECURITY"** to expand.

**Container tab:**

**General:**
- **Container port:** `8080`
- **Request timeout:** `60` seconds

**Resources:**
- **Memory:** `512 MiB`
- **CPU:** `1`

**Execution environment:**
- Leave as default (Gen 2)

### Step 6: Add Environment Variables

Click **"VARIABLES & SECRETS"** tab.

**Environment Variables:**

Click **"+ ADD VARIABLE"**

- **Name 1:** `BACKEND_URL`
- **Value 1:** `https://best-galaxy-backend-xxxxx-uc.a.run.app` (paste your backend URL from Step 1)

**Important:** Replace with your actual backend URL!

### Step 7: Review and Deploy

1. Scroll down and click **"CREATE"**
2. Wait 2-3 minutes for deployment
3. You'll see a progress indicator

### Step 8: Get Frontend URL

Once deployed:

1. You'll see a green checkmark ✓
2. The service URL will be displayed at the top
3. Copy the URL (e.g., `https://best-galaxy-frontend-xxxxx-uc.a.run.app`)

### Step 9: Test Your Application

1. Click on the frontend URL
2. You should see the BEST Galaxy Assessment homepage
3. Test the application:
   - Create an account
   - Complete an assessment
   - View results
   - Test payment flow

---

## Part 3: Verify Deployment

### Check Service Status

1. Go to https://console.cloud.google.com/run
2. Click on `best-galaxy-frontend`
3. Check:
   - **Status:** Should show green checkmark
   - **Last deployed:** Should show recent timestamp
   - **Revisions:** Should show 100% traffic to latest revision

### View Logs

1. In the service details page, click **"LOGS"** tab
2. You should see:
   - Nginx startup logs
   - HTTP requests
   - No errors

### Test API Connectivity

Open browser console (F12) and visit your frontend URL:

1. Check Network tab
2. API calls to `/api/*` should succeed
3. No CORS errors

---

## Part 4: Update Frontend (After Changes)

When you make changes to the frontend code:

### Step 1: Rebuild Docker Image

```bash
cd /home/ubuntu/Documents/backend-scoring-engine/frontend
sudo docker build -t best-galaxy-frontend:latest .
```

### Step 2: Tag and Push

```bash
sudo docker tag best-galaxy-frontend:latest \
  us-central1-docker.pkg.dev/eighth-etching-491401-e5/best-galaxy-backend/frontend:latest

sudo docker push us-central1-docker.pkg.dev/eighth-etching-491401-e5/best-galaxy-backend/frontend:latest
```

### Step 3: Deploy New Revision via Console

1. Go to https://console.cloud.google.com/run
2. Click on `best-galaxy-frontend`
3. Click **"EDIT & DEPLOY NEW REVISION"** button
4. The new image will be automatically detected
5. Click **"DEPLOY"**
6. Wait 1-2 minutes for rollout

**Or use command line:**
```bash
gcloud run services update best-galaxy-frontend \
  --region us-central1 \
  --project eighth-etching-491401-e5
```

---

## Troubleshooting

### Frontend Shows 502 Bad Gateway

**Cause:** Nginx not starting or wrong port

**Fix:**
1. Check logs in Cloud Run console
2. Verify `nginx.conf` has `listen 8080;`
3. Verify Dockerfile exposes port 8080

### API Calls Fail (CORS Errors)

**Cause:** Backend URL not set correctly

**Fix:**
1. Go to Cloud Run console
2. Click `best-galaxy-frontend`
3. Click **"EDIT & DEPLOY NEW REVISION"**
4. Check **"VARIABLES & SECRETS"** tab
5. Verify `BACKEND_URL` is set to correct backend URL
6. Click **"DEPLOY"**

### Frontend Shows Blank Page

**Cause:** React build failed or files not copied

**Fix:**
1. Check build logs from Docker build
2. Verify `npm run build` succeeded
3. Rebuild image:
   ```bash
   cd frontend
   sudo docker build -t best-galaxy-frontend:latest .
   ```

### Can't Access Backend API

**Cause:** Nginx proxy misconfigured

**Fix:**
1. Check `frontend/nginx.conf`
2. Verify proxy_pass points to `$BACKEND_URL`
3. Verify location `/api/` block exists
4. Rebuild and redeploy

### Image Push Fails

**Cause:** Not authenticated or using sudo without credentials

**Fix:**
```bash
# Re-authenticate
export PATH="/tmp/google-cloud-sdk/bin:$PATH"
gcloud auth login
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push without sudo (if in docker group)
docker push us-central1-docker.pkg.dev/eighth-etching-491401-e5/best-galaxy-backend/frontend:latest

# Or authenticate sudo
sudo /tmp/google-cloud-sdk/bin/gcloud auth login
sudo /tmp/google-cloud-sdk/bin/gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## Configuration Reference

### Frontend Service Configuration

| Setting | Value |
|---------|-------|
| Service Name | `best-galaxy-frontend` |
| Region | `us-central1` |
| Container Port | `8080` |
| Memory | `512 MiB` |
| CPU | `1` |
| Min Instances | `0` |
| Max Instances | `5` |
| Timeout | `60 seconds` |
| Authentication | Allow unauthenticated |

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `BACKEND_URL` | `https://best-galaxy-backend-xxxxx.run.app` | Backend API URL |

### Image Path

```
us-central1-docker.pkg.dev/eighth-etching-491401-e5/best-galaxy-backend/frontend:latest
```

---

## Cost Optimization

### Current Configuration

- **Scales to zero:** No cost when idle
- **512 MiB memory:** Lower cost than backend
- **Request-based billing:** Only pay during active requests

### Expected Costs

- **Low traffic:** $1-5/month
- **Medium traffic:** $5-15/month
- **High traffic:** $15-30/month

### Optimization Tips

1. **Enable Cloud CDN** (in console):
   - Go to service details
   - Click "EDIT & DEPLOY NEW REVISION"
   - Under "Networking" → Enable Cloud CDN
   - Caches static assets at edge locations

2. **Set appropriate min instances:**
   - Keep at 0 for development
   - Set to 1 for production (faster response, but costs ~$10/month)

3. **Monitor usage:**
   - Go to https://console.cloud.google.com/run
   - Click on service
   - Check "METRICS" tab

---

## Custom Domain (Optional)

### Add Custom Domain

1. Go to https://console.cloud.google.com/run
2. Click on `best-galaxy-frontend`
3. Click **"MANAGE CUSTOM DOMAINS"** tab
4. Click **"ADD MAPPING"**
5. Select or add your domain
6. Follow DNS configuration instructions
7. Wait for SSL certificate provisioning (5-15 minutes)

### Update Backend CORS

After adding custom domain, update backend to allow it:

1. Edit `scoring_engine/api.py`
2. Add your domain to CORS origins:
   ```python
   allow_origins=[
       "https://yourdomain.com",
       "https://best-galaxy-frontend-xxxxx.run.app"
   ]
   ```
3. Rebuild and redeploy backend

---

## Monitoring and Alerts

### View Metrics

1. Go to https://console.cloud.google.com/run
2. Click on `best-galaxy-frontend`
3. Click **"METRICS"** tab
4. View:
   - Request count
   - Request latency
   - Container instance count
   - CPU/Memory utilization

### Set Up Alerts

1. Go to https://console.cloud.google.com/monitoring/alerting
2. Click **"+ CREATE POLICY"**
3. Configure alert:
   - **Resource:** Cloud Run Revision
   - **Metric:** Request latency or Error rate
   - **Condition:** e.g., Latency > 2 seconds
   - **Notification:** Email or SMS

---

## Security Best Practices

### Current Setup

✅ HTTPS enforced automatically
✅ Unauthenticated access (required for public app)
✅ No secrets in environment variables
✅ Nginx security headers configured

### Additional Security

1. **Enable Cloud Armor** (DDoS protection):
   - Go to Network Security → Cloud Armor
   - Create security policy
   - Attach to Cloud Run service

2. **Set up rate limiting:**
   - Configure in nginx.conf
   - Or use Cloud Armor rate limiting

3. **Monitor for suspicious activity:**
   - Check logs regularly
   - Set up alerts for unusual patterns

---

## Complete Deployment Checklist

### Backend Deployment
- [ ] Backend Docker image built
- [ ] Backend pushed to Artifact Registry
- [ ] Backend deployed to Cloud Run
- [ ] Backend URL obtained
- [ ] Secrets configured in Secret Manager
- [ ] Backend health check passing

### Frontend Deployment
- [ ] Frontend Docker image built
- [ ] Frontend pushed to Artifact Registry
- [ ] Frontend deployed to Cloud Run
- [ ] `BACKEND_URL` environment variable set
- [ ] Frontend accessible via URL
- [ ] API calls to backend working

### Testing
- [ ] Homepage loads correctly
- [ ] User signup works
- [ ] User login works
- [ ] Assessment completion works
- [ ] Results display correctly
- [ ] Payment flow works
- [ ] PDF downloads work

### Production Readiness
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active
- [ ] Monitoring and alerts set up
- [ ] Backup strategy in place
- [ ] Cost alerts configured

---

## Summary

**Your frontend is now deployed!**

**Frontend URL:** `https://best-galaxy-frontend-xxxxx-uc.a.run.app`
**Backend URL:** `https://best-galaxy-backend-xxxxx-uc.a.run.app`

**Next Steps:**
1. Test the complete application flow
2. Update Stripe webhook URL to backend
3. Configure custom domain (optional)
4. Set up monitoring and alerts
5. Share the app with users!

**Support Resources:**
- Cloud Run docs: https://cloud.google.com/run/docs
- Artifact Registry: https://cloud.google.com/artifact-registry/docs
- Monitoring: https://cloud.google.com/monitoring/docs
