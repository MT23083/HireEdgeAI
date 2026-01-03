#!/bin/bash
# AWS App Runner Deployment Script

set -e

# Configuration
REGION="us-east-1"
ECR_REPO="hireedgeai-backend"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_TAG="latest"

echo "🚀 Starting AWS App Runner Deployment..."

# Step 1: Create ECR repository (if not exists)
echo "📦 Checking ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION 2>/dev/null || \
  aws ecr create-repository --repository-name $ECR_REPO --region $REGION

# Step 2: Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Step 3: Build Docker image
echo "🏗️  Building Docker image..."
docker build -t $ECR_REPO:$IMAGE_TAG .

# Step 4: Tag image
echo "🏷️  Tagging image..."
docker tag $ECR_REPO:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPO:$IMAGE_TAG

# Step 5: Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_REGISTRY/$ECR_REPO:$IMAGE_TAG

echo "✅ Docker image pushed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Go to AWS Console → App Runner"
echo "2. Create new service"
echo "3. Source: ECR"
echo "4. Select image: $ECR_REGISTRY/$ECR_REPO:$IMAGE_TAG"
echo "5. Configure environment variables (see DEPLOY.md)"
echo "6. Deploy!"

