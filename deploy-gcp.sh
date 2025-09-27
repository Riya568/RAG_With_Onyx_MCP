#!/bin/bash

# GCP Deployment Script for Onyx
# This script deploys Onyx to Google Cloud Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"onyx-project"}
REGION=${GCP_REGION:-"us-central1"}
BUCKET_NAME=${GCP_BUCKET_NAME:-"onyx-files-$PROJECT_ID"}

echo -e "${GREEN}🚀 Starting GCP deployment for Onyx${NC}"

# Step 1: Set up GCP project
echo -e "${YELLOW}📋 Setting up GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Step 2: Create GCS bucket
echo -e "${YELLOW}🪣 Creating Cloud Storage bucket...${NC}"
gsutil mb gs://$BUCKET_NAME || echo "Bucket already exists"
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Step 3: Create service account
echo -e "${YELLOW}👤 Creating service account...${NC}"
gcloud iam service-accounts create onyx-service-account \
    --display-name="Onyx Service Account" \
    --description="Service account for Onyx application" || echo "Service account already exists"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:onyx-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download service account key
echo -e "${YELLOW}🔑 Creating service account key...${NC}"
gcloud iam service-accounts keys create onyx-key.json \
    --iam-account=onyx-service-account@$PROJECT_ID.iam.gserviceaccount.com

# Step 4: Build and deploy to Cloud Run
echo -e "${YELLOW}🏗️ Building and deploying to Cloud Run...${NC}"
cd backend

# Build the image
gcloud builds submit --tag gcr.io/$PROJECT_ID/onyx-backend .

# Deploy to Cloud Run
gcloud run deploy onyx-backend \
    --image gcr.io/$PROJECT_ID/onyx-backend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 1 \
    --set-env-vars "FILE_STORE_TYPE=gcp,GCP_PROJECT_ID=$PROJECT_ID,GCP_BUCKET_NAME=$BUCKET_NAME" \
    --service-account onyx-service-account@$PROJECT_ID.iam.gserviceaccount.com

# Step 5: Set up Cloud SQL (PostgreSQL)
echo -e "${YELLOW}🗄️ Setting up Cloud SQL...${NC}"
gcloud sql instances create onyx-postgres \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=password || echo "Cloud SQL instance already exists"

gcloud sql databases create onyx --instance=onyx-postgres || echo "Database already exists"

# Step 6: Set up Redis (Memorystore)
echo -e "${YELLOW}🔴 Setting up Redis...${NC}"
gcloud redis instances create onyx-redis \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_7_0 || echo "Redis instance already exists"

# Step 7: Get deployment URLs
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Onyx Backend URL:${NC}"
gcloud run services describe onyx-backend --platform managed --region $REGION --format 'value(status.url)'

echo -e "${GREEN}📊 Cloud SQL connection:${NC}"
gcloud sql instances describe onyx-postgres --format 'value(connectionName)'

echo -e "${GREEN}🔴 Redis connection:${NC}"
gcloud redis instances describe onyx-redis --region $REGION --format 'value(host)'

echo -e "${GREEN}🎉 Onyx is now running on GCP!${NC}"
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "1. Update your environment variables with the connection details above"
echo -e "2. Run database migrations: alembic upgrade head"
echo -e "3. Access your application at the Cloud Run URL"
