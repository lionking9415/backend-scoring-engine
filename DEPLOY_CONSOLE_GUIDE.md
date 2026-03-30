# Google Cloud Console Deployment Guide (Web UI)

This guide walks you through deploying the BEST Galaxy Assessment application using the **Google Cloud Console web interface** (no command line required).

## Overview

You'll deploy two services:
1. **Backend API** - Python FastAPI server
2. **Frontend** - React application

**Total Time:** ~30-40 minutes

---

## Part 1: Initial Setup (10 minutes)

### Step 1: Create Google Cloud Account

1. Go to https://cloud.google.com
2. Click **"Get started for free"** or **"Console"**
3. Sign in with your Google account
4. Complete the billing setup (required for Cloud Run)
   - You get $300 free credit for 90 days
   - Credit card required but won't be charged during free trial

### Step 2: Create a New Project

1. Go to https://console.cloud.google.com
2. Click the **project dropdown** at the top (next to "Google Cloud")
3. Click **"NEW PROJECT"**
4. Enter project details:
   - **Project name:** `best-galaxy-assessment`
   - **Project ID:** Will auto-generate (e.g., `best-galaxy-assessment-123456`)
   - **Location:** Leave as default
5. Click **"CREATE"**
6. Wait for project creation (~30 seconds)
7. Click **"SELECT PROJECT"** when prompted

### Step 3: Enable Required APIs

1. In the search bar at top, type: **"Cloud Run API"**
2. Click **"Cloud Run API"**
3. Click **"ENABLE"**
4. Repeat for these APIs:
   - **"Cloud Build API"** - Enable
   - **"Secret Manager API"** - Enable
   - **"Container Registry API"** - Enable

---

## Part 2: Store Secrets (10 minutes)

### Step 1: Open Secret Manager

1. In the left menu (☰), scroll down to **"Security"**
2. Click **"Secret Manager"**
3. If prompted, click **"ENABLE SECRET MANAGER API"**

### Step 2: Create Supabase URL Secret

1. Click **"+ CREATE SECRET"**
2. Fill in:
   - **Name:** `SUPABASE_URL`
   - **Secret value:** Paste your Supabase project URL
     - Find it at: https://app.supabase.com → Your Project → Settings → API
     - Example: `https://abcdefgh.supabase.co`
3. Click **"CREATE SECRET"**

### Step 3: Create Supabase Key Secret

1. Click **"+ CREATE SECRET"** again
2. Fill in:
   - **Name:** `SUPABASE_KEY`
   - **Secret value:** Paste your Supabase anon/service key
     - Find it at: https://app.supabase.com → Your Project → Settings → API
     - Use the `anon` `public` key or `service_role` key
3. Click **"CREATE SECRET"**

### Step 4: Create Stripe Secret Key

1. Click **"+ CREATE SECRET"**
2. Fill in:
   - **Name:** `STRIPE_SECRET_KEY`
   - **Secret value:** Paste your Stripe secret key
     - Find it at: https://dashboard.stripe.com/apikeys
     - Starts with `sk_test_` or `sk_live_`
3. Click **"CREATE SECRET"**

### Step 5: Create Stripe Webhook Secret

1. Click **"+ CREATE SECRET"**
2. Fill in:
   - **Name:** `STRIPE_WEBHOOK_SECRET`
   - **Secret value:** Paste your Stripe webhook signing secret
     - Find it at: https://dashboard.stripe.com/webhooks
     - Click on your webhook → **Signing secret**
     - Starts with `whsec_`
3. Click **"CREATE SECRET"**

### Step 6: Create OpenAI API Key Secret

1. Click **"+ CREATE SECRET"**
2. Fill in:
   - **Name:** `OPENAI_API_KEY`
   - **Secret value:** Paste your OpenAI API key
     - Find it at: https://platform.openai.com/api-keys
     - Starts with `sk-`
3. Click **"CREATE SECRET"**

**You should now have 5 secrets created.**

---

## Part 3: Deploy Backend API (10 minutes)

### Step 1: Open Cloud Run

1. In the left menu (☰), scroll to **"Serverless"**
2. Click **"Cloud Run"**

### Step 2: Create Backend Service

1. Click **"+ CREATE SERVICE"**
2. Select **"Continuously deploy from a repository (source-based)"**
3. Click **"SET UP WITH CLOUD BUILD"**

### Step 3: Connect Repository

**Option A: Using GitHub (Recommended)**

1. Click **"GitHub"**
2. Click **"Authenticate"** and sign in to GitHub
3. Select your repository or click **"Add repository"**
4. Select the repository containing your code
5. Click **"NEXT"**

**Option B: Upload Code Directly**

1. Click **"Upload files"**
2. Upload your backend code as a ZIP file
3. Click **"NEXT"**

### Step 4: Configure Build

1. **Branch:** Select `main` or `master`
2. **Build Type:** Select **"Dockerfile"**
3. **Source location:** `/Dockerfile` (root directory)
4. Click **"SAVE"**

### Step 5: Configure Service

1. **Service name:** `best-galaxy-backend`
2. **Region:** Select closest to your users (e.g., `us-central1`)
3. **CPU allocation:** Select **"CPU is only allocated during request processing"**
4. **Autoscaling:**
   - **Minimum instances:** `0`
   - **Maximum instances:** `10`
5. **Ingress:** Select **"Allow all traffic"**
6. **Authentication:** Select **"Allow unauthenticated invocations"**

### Step 6: Configure Container

Click **"CONTAINER, VARIABLES & SECRETS, CONNECTIONS, SECURITY"**

**Container tab:**
- **Container port:** `8080`
- **Memory:** `1 GiB`
- **CPU:** `1`
- **Request timeout:** `300` seconds

**Variables & Secrets tab:**

1. Click **"+ ADD VARIABLE"**
   - **Name:** `ENVIRONMENT`
   - **Value:** `production`

2. Click **"REFERENCE A SECRET"** (do this 5 times for each secret):

   **Secret 1:**
   - **Select secret:** `SUPABASE_URL`
   - **Reference method:** "Exposed as environment variable"
   - **Environment variable name:** `SUPABASE_URL`
   - **Version:** `latest`

   **Secret 2:**
   - **Select secret:** `SUPABASE_KEY`
   - **Environment variable name:** `SUPABASE_KEY`
   - **Version:** `latest`

   **Secret 3:**
   - **Select secret:** `STRIPE_SECRET_KEY`
   - **Environment variable name:** `STRIPE_SECRET_KEY`
   - **Version:** `latest`

   **Secret 4:**
   - **Select secret:** `STRIPE_WEBHOOK_SECRET`
   - **Environment variable name:** `STRIPE_WEBHOOK_SECRET`
   - **Version:** `latest`

   **Secret 5:**
   - **Select secret:** `OPENAI_API_KEY`
   - **Environment variable name:** `OPENAI_API_KEY`
   - **Version:** `latest`

### Step 7: Deploy

1. Click **"CREATE"** at the bottom
2. Wait for deployment (5-10 minutes)
3. You'll see a green checkmark when complete
4. **Copy the backend URL** (e.g., `https://best-galaxy-backend-xxxxx.run.app`)
   - You'll need this for the frontend deployment

---

## Part 4: Deploy Frontend (10 minutes)

### Step 1: Create Frontend Service

1. In Cloud Run, click **"+ CREATE SERVICE"**
2. Select **"Continuously deploy from a repository"**
3. Click **"SET UP WITH CLOUD BUILD"**

### Step 2: Connect Repository

1. Select the same repository as before
2. Click **"NEXT"**

### Step 3: Configure Build

1. **Branch:** Select `main` or `master`
2. **Build Type:** Select **"Dockerfile"**
3. **Source location:** `/frontend/Dockerfile`
4. Click **"SAVE"**

### Step 4: Configure Service

1. **Service name:** `best-galaxy-frontend`
2. **Region:** Same as backend (e.g., `us-central1`)
3. **CPU allocation:** **"CPU is only allocated during request processing"**
4. **Autoscaling:**
   - **Minimum instances:** `0`
   - **Maximum instances:** `5`
5. **Ingress:** **"Allow all traffic"**
6. **Authentication:** **"Allow unauthenticated invocations"**

### Step 5: Configure Container

Click **"CONTAINER, VARIABLES & SECRETS, CONNECTIONS, SECURITY"**

**Container tab:**
- **Container port:** `8080`
- **Memory:** `512 MiB`
- **CPU:** `1`
- **Request timeout:** `60` seconds

**Variables & Secrets tab:**

Click **"+ ADD VARIABLE"**
- **Name:** `BACKEND_URL`
- **Value:** Paste your backend URL from Part 3, Step 7
  - Example: `https://best-galaxy-backend-xxxxx.run.app`

### Step 6: Deploy

1. Click **"CREATE"**
2. Wait for deployment (5-10 minutes)
3. When complete, **copy the frontend URL**
   - Example: `https://best-galaxy-frontend-xxxxx.run.app`

---

## Part 5: Post-Deployment Configuration (5 minutes)

### Step 1: Update Stripe Webhook

1. Go to https://dashboard.stripe.com/webhooks
2. Click on your webhook endpoint (or create new one)
3. Update the **Endpoint URL** to:
   ```
   https://your-backend-url.run.app/api/v1/payment/webhook
   ```
   - Replace `your-backend-url` with your actual backend URL
4. Ensure these events are selected:
   - `checkout.session.completed`
5. Click **"Update endpoint"**
6. Copy the **Signing secret** (starts with `whsec_`)
7. If different from before, update the `STRIPE_WEBHOOK_SECRET` in Secret Manager

### Step 2: Test Your Application

1. Open your **frontend URL** in a browser
2. Try creating an account
3. Complete an assessment
4. Test the payment flow

---

## Monitoring & Logs

### View Logs

1. Go to **Cloud Run** in the console
2. Click on your service (backend or frontend)
3. Click the **"LOGS"** tab
4. You'll see real-time logs of requests and errors

### View Metrics

1. In the service details page, click **"METRICS"** tab
2. View:
   - Request count
   - Request latency
   - Container instance count
   - Memory and CPU usage

---

## Updating Your Application

### Update Backend

1. Make code changes in your repository
2. Push to GitHub (or your connected repo)
3. Cloud Build will automatically rebuild and deploy
4. Or manually trigger:
   - Go to **Cloud Run** → Select service
   - Click **"EDIT & DEPLOY NEW REVISION"**
   - Click **"DEPLOY"**

### Update Frontend

Same process as backend - push changes and Cloud Build auto-deploys.

---

## Troubleshooting

### Build Failed

1. Go to **Cloud Build** in left menu
2. Click **"History"**
3. Find your failed build
4. Click on it to see error logs
5. Common issues:
   - Missing Dockerfile
   - Wrong Dockerfile path
   - Build timeout (increase in build settings)

### Service Not Responding

1. Check **Logs** tab in Cloud Run
2. Look for error messages
3. Common issues:
   - Wrong port (must be 8080)
   - Missing environment variables
   - Secret access denied

### Secret Access Denied

1. Go to **IAM & Admin** → **IAM**
2. Find the service account (ends with `@cloudbuild.gserviceaccount.com`)
3. Click **"Edit"**
4. Add role: **"Secret Manager Secret Accessor"**
5. Click **"SAVE"**

### Frontend Can't Reach Backend

1. Verify `BACKEND_URL` environment variable is set correctly
2. Check backend service is running
3. Verify backend allows unauthenticated requests

---

## Cost Management

### View Current Costs

1. Go to **Billing** in left menu
2. Click **"Reports"**
3. Filter by:
   - Service: Cloud Run
   - Time range: This month

### Set Budget Alerts

1. Go to **Billing** → **"Budgets & alerts"**
2. Click **"CREATE BUDGET"**
3. Set:
   - **Budget name:** `Cloud Run Monthly Budget`
   - **Budget amount:** `$20` (or your limit)
   - **Alert threshold:** `50%, 90%, 100%`
4. Click **"FINISH"**

### Reduce Costs

1. Set **minimum instances to 0** (scales to zero when idle)
2. Reduce **maximum instances** if traffic is low
3. Lower **memory allocation** if possible
4. Enable **CPU throttling** when not processing requests

---

## Security Best Practices

### 1. Enable Cloud Armor (Optional)

1. Go to **Network Security** → **Cloud Armor**
2. Create security policy for DDoS protection

### 2. Set Up IAM Roles

1. Go to **IAM & Admin** → **IAM**
2. Review service account permissions
3. Follow principle of least privilege

### 3. Enable Audit Logs

1. Go to **IAM & Admin** → **Audit Logs**
2. Enable for Cloud Run
3. Review logs regularly

---

## Additional Resources

- **Cloud Run Documentation:** https://cloud.google.com/run/docs
- **Cloud Build Documentation:** https://cloud.google.com/build/docs
- **Secret Manager Documentation:** https://cloud.google.com/secret-manager/docs
- **Pricing Calculator:** https://cloud.google.com/products/calculator

---

## Quick Reference

### Backend Service Settings
- **Name:** `best-galaxy-backend`
- **Port:** `8080`
- **Memory:** `1 GiB`
- **CPU:** `1`
- **Min instances:** `0`
- **Max instances:** `10`
- **Timeout:** `300s`

### Frontend Service Settings
- **Name:** `best-galaxy-frontend`
- **Port:** `8080`
- **Memory:** `512 MiB`
- **CPU:** `1`
- **Min instances:** `0`
- **Max instances:** `5`
- **Timeout:** `60s`

### Required Secrets
1. `SUPABASE_URL`
2. `SUPABASE_KEY`
3. `STRIPE_SECRET_KEY`
4. `STRIPE_WEBHOOK_SECRET`
5. `OPENAI_API_KEY`

---

## Support

If you encounter issues:

1. **Check logs first** (Cloud Run → Service → Logs tab)
2. **Verify secrets** are created and accessible
3. **Check build history** (Cloud Build → History)
4. **Review IAM permissions** (IAM & Admin → IAM)
5. **Test locally** with Docker before deploying

For additional help, see the [full deployment documentation](./DEPLOYMENT.md).
