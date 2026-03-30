#!/bin/bash
# Google Cloud Run Deployment Script
# This script deploys both backend and frontend to Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
BACKEND_SERVICE_NAME="best-galaxy-backend"
FRONTEND_SERVICE_NAME="best-galaxy-frontend"

echo -e "${GREEN}=== BEST Galaxy Assessment - Google Cloud Run Deployment ===${NC}\n"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}Not logged in to gcloud. Running login...${NC}"
    gcloud auth login
fi

# Set project
echo -e "${YELLOW}Setting GCP project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "\n${YELLOW}Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# Deploy Backend
echo -e "\n${GREEN}=== Deploying Backend API ===${NC}"
echo "Building and deploying backend to Cloud Run..."

gcloud run deploy ${BACKEND_SERVICE_NAME} \
    --source . \
    --platform managed \
    --region ${REGION} \
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
BACKEND_URL=$(gcloud run services describe ${BACKEND_SERVICE_NAME} \
    --region ${REGION} \
    --format 'value(status.url)')

echo -e "${GREEN}✓ Backend deployed successfully!${NC}"
echo -e "Backend URL: ${BACKEND_URL}"

# Deploy Frontend
echo -e "\n${GREEN}=== Deploying Frontend ===${NC}"
echo "Building and deploying frontend to Cloud Run..."

cd frontend

# Update package.json proxy to use backend URL
echo -e "${YELLOW}Configuring frontend to use backend: ${BACKEND_URL}${NC}"

gcloud run deploy ${FRONTEND_SERVICE_NAME} \
    --source . \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --timeout 60 \
    --set-env-vars "BACKEND_URL=${BACKEND_URL}"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe ${FRONTEND_SERVICE_NAME} \
    --region ${REGION} \
    --format 'value(status.url)')

cd ..

echo -e "\n${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}✓ Backend URL:  ${BACKEND_URL}${NC}"
echo -e "${GREEN}✓ Frontend URL: ${FRONTEND_URL}${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Update Stripe webhook URL to: ${BACKEND_URL}/api/v1/payment/webhook"
echo "2. Update CORS settings if needed"
echo "3. Test the application at: ${FRONTEND_URL}"
echo -e "\n${YELLOW}To view logs:${NC}"
echo "  Backend:  gcloud run services logs tail ${BACKEND_SERVICE_NAME} --region ${REGION}"
echo "  Frontend: gcloud run services logs tail ${FRONTEND_SERVICE_NAME} --region ${REGION}"
