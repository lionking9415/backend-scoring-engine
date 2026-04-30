#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Deploy BEST Galaxy to Google Cloud Run
#
# USAGE
#   ./deploy.sh [--project PROJECT_ID] [--region REGION]
#
# FIRST-TIME SETUP
#   1. Install gcloud CLI:  https://cloud.google.com/sdk/docs/install
#   2. Authenticate:        gcloud auth login
#   3. Set your project:    gcloud config set project YOUR_PROJECT_ID
#   4. Enable APIs:
#        gcloud services enable \
#          run.googleapis.com \
#          artifactregistry.googleapis.com \
#          cloudbuild.googleapis.com
#   5. Create the Artifact Registry repo (once):
#        gcloud artifacts repositories create best-galaxy \
#          --repository-format=docker \
#          --location=us-central1 \
#          --description="BEST Galaxy Docker images"
#
# WHAT THIS SCRIPT DOES
#   1. Builds & pushes the backend image
#   2. Deploys backend to Cloud Run and captures its URL
#   3. Builds & pushes the frontend image (with BACKEND_URL baked in as nginx proxy target)
#   4. Deploys frontend to Cloud Run (public)
#   5. Updates the backend's ALLOWED_ORIGINS to the frontend URL
#   6. Prints the live frontend URL
#
# SECRETS
#   All sensitive env vars are passed to Cloud Run via --set-env-vars / --set-secrets.
#   They are NEVER baked into the Docker image.
#   Load them from .env before running this script, or set them in your shell.
# =============================================================================

set -euo pipefail

# ── Configurable defaults ────────────────────────────────────────────────────
PROJECT_ID="${GCLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCLOUD_REGION:-us-central1}"
REPO="best-galaxy"
BACKEND_SERVICE="best-galaxy-backend"
FRONTEND_SERVICE="best-galaxy-frontend"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"

# Parse CLI overrides
while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --region)  REGION="$2";     shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Validation ───────────────────────────────────────────────────────────────
if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: GCP project ID not set."
  echo "       Run: gcloud config set project YOUR_PROJECT_ID"
  echo "       Or:  export GCLOUD_PROJECT=YOUR_PROJECT_ID"
  exit 1
fi

# Required secrets — must be set in environment before running this script.
REQUIRED_VARS=(
  SUPABASE_URL
  SUPABASE_ANON_KEY
  OPENAI_API_KEY
  STRIPE_SECRET_KEY
  STRIPE_PUBLISHABLE_KEY
  STRIPE_WEBHOOK_SECRET
  STRIPE_PRICE_ID_COSMIC_BUNDLE
  STRIPE_PRICE_ID_PERSONAL_LIFESTYLE
  STRIPE_PRICE_ID_STUDENT_SUCCESS
  STRIPE_PRICE_ID_PROFESSIONAL_LEADERSHIP
  STRIPE_PRICE_ID_FAMILY_ECOSYSTEM
  ADMIN_API_TOKEN
)
MISSING=()
for v in "${REQUIRED_VARS[@]}"; do
  [[ -z "${!v:-}" ]] && MISSING+=("$v")
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "ERROR: The following required env vars are not set:"
  for v in "${MISSING[@]}"; do echo "         $v"; done
  echo ""
  echo "Tip: source your .env file first — but never commit .env to git."
  echo "     set -a && source .env && set +a"
  exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   BEST Galaxy — Google Cloud Run Deployment          ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Project : ${PROJECT_ID}"
echo "║  Region  : ${REGION}"
echo "║  Registry: ${REGISTRY}"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Authenticate Docker with Artifact Registry ───────────────────────────────
echo "▶ Configuring Docker authentication for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — Build & push backend image
# ═════════════════════════════════════════════════════════════════════════════
BACKEND_IMAGE="${REGISTRY}/${BACKEND_SERVICE}:latest"
echo ""
echo "▶ Building backend image: ${BACKEND_IMAGE}"
docker build \
  --platform linux/amd64 \
  -t "${BACKEND_IMAGE}" \
  -f Dockerfile \
  .

echo "▶ Pushing backend image..."
docker push "${BACKEND_IMAGE}"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — Deploy backend to Cloud Run
# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo "▶ Deploying backend to Cloud Run (${BACKEND_SERVICE})..."

gcloud run deploy "${BACKEND_SERVICE}" \
  --image="${BACKEND_IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300 \
  --concurrency=80 \
  --no-allow-unauthenticated \
  --set-env-vars="\
SUPABASE_URL=${SUPABASE_URL},\
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY},\
OPENAI_API_KEY=${OPENAI_API_KEY},\
STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY},\
STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY},\
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET},\
STRIPE_PRICE_ID=${STRIPE_PRICE_ID_COSMIC_BUNDLE},\
STRIPE_PRICE_ID_COSMIC_BUNDLE=${STRIPE_PRICE_ID_COSMIC_BUNDLE},\
STRIPE_PRICE_ID_PERSONAL_LIFESTYLE=${STRIPE_PRICE_ID_PERSONAL_LIFESTYLE},\
STRIPE_PRICE_ID_STUDENT_SUCCESS=${STRIPE_PRICE_ID_STUDENT_SUCCESS},\
STRIPE_PRICE_ID_PROFESSIONAL_LEADERSHIP=${STRIPE_PRICE_ID_PROFESSIONAL_LEADERSHIP},\
STRIPE_PRICE_ID_FAMILY_ECOSYSTEM=${STRIPE_PRICE_ID_FAMILY_ECOSYSTEM},\
ADMIN_API_TOKEN=${ADMIN_API_TOKEN}" \
  --quiet

# Capture the backend URL
BACKEND_URL=$(gcloud run services describe "${BACKEND_SERVICE}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo "✓ Backend deployed: ${BACKEND_URL}"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — Make backend publicly reachable for the frontend nginx proxy
# (Cloud Run services are private by default; the frontend container
#  calls the backend via server-side proxy, so it needs unauthenticated access
#  OR we grant the frontend's service account. The simplest option for now:
#  allow-unauthenticated on the backend. If you want IAM auth between services,
#  set up a service account and Workload Identity instead.)
# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo "▶ Granting public access to backend (for frontend nginx proxy)..."
gcloud run services add-iam-policy-binding "${BACKEND_SERVICE}" \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --quiet

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — Build & push frontend image (with BACKEND_URL baked into nginx)
# ═════════════════════════════════════════════════════════════════════════════
FRONTEND_IMAGE="${REGISTRY}/${FRONTEND_SERVICE}:latest"
echo ""
echo "▶ Building frontend image (BACKEND_URL=${BACKEND_URL}): ${FRONTEND_IMAGE}"
docker build \
  --platform linux/amd64 \
  -t "${FRONTEND_IMAGE}" \
  -f frontend/Dockerfile \
  frontend/

echo "▶ Pushing frontend image..."
docker push "${FRONTEND_IMAGE}"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 — Deploy frontend to Cloud Run (public)
# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo "▶ Deploying frontend to Cloud Run (${FRONTEND_SERVICE})..."

gcloud run deploy "${FRONTEND_SERVICE}" \
  --image="${FRONTEND_IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=60 \
  --concurrency=1000 \
  --allow-unauthenticated \
  --set-env-vars="BACKEND_URL=${BACKEND_URL}" \
  --quiet

FRONTEND_URL=$(gcloud run services describe "${FRONTEND_SERVICE}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo "✓ Frontend deployed: ${FRONTEND_URL}"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 6 — Update backend ALLOWED_ORIGINS to the frontend URL
# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo "▶ Locking backend CORS to frontend origin: ${FRONTEND_URL}"
gcloud run services update "${BACKEND_SERVICE}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --update-env-vars="ALLOWED_ORIGINS=${FRONTEND_URL}" \
  --quiet

# ═════════════════════════════════════════════════════════════════════════════
# DONE
# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Deployment Complete!                               ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Frontend : ${FRONTEND_URL}"
echo "║  Backend  : ${BACKEND_URL}"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "⚠  Stripe Webhook — update your Stripe dashboard:"
echo "   Endpoint URL: ${BACKEND_URL}/api/v1/payment/webhook"
echo "   Events:       checkout.session.completed"
echo ""
echo "⚠  Stripe Redirect URLs — if needed, add to Stripe's allowed list:"
echo "   Success: ${FRONTEND_URL}/success"
echo "   Cancel:  ${FRONTEND_URL}/"
echo ""
