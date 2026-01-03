# AWS App Runner Deployment Guide

## Prerequisites

1. **AWS Account** with CLI configured
2. **AWS Activate Credits** (recommended for startups)
3. **Docker** installed locally
4. **AWS CLI** installed and configured

## Quick Start

### 1. Build and Push Docker Image

```bash
# Make script executable
chmod +x deploy-apprunner.sh

# Run deployment script
./deploy-apprunner.sh
```

This will:
- Create ECR repository (if needed)
- Build Docker image
- Push to AWS ECR

### 2. Create App Runner Service (AWS Console)

1. Go to **AWS Console → App Runner**
2. Click **"Create service"**
3. **Source**: Choose "Container registry" → Amazon ECR
4. **Container image URI**: 
   ```
   <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/hireedgeai-backend:latest
   ```
5. **Deployment trigger**: Manual (or Automatic for CI/CD)

### 3. Configure Service Settings

**Compute:**
- CPU: 1 vCPU
- Memory: 2 GB
- Instance: Auto scaling enabled (1-10 instances)

**Network:**
- Port: 8000
- Health check: `/api/health`

**Environment Variables:**
Add these from AWS Secrets Manager or directly:

```
HOST=0.0.0.0
PORT=8000
DEBUG=false
FRONTEND_URL=https://yourdomain.com
OPENAI_API_KEY=<from-secrets-manager>
OPENAI_MODEL=gpt-4o-mini
RAZORPAY_KEY_ID=<from-secrets-manager>
RAZORPAY_KEY_SECRET=<from-secrets-manager>
```

### 4. Create Secrets in AWS Secrets Manager

```bash
# Create secret for OpenAI API key
aws secretsmanager create-secret \
  --name hireedgeai/openai-api-key \
  --secret-string "your-openai-api-key"

# Create secret for Razorpay
aws secretsmanager create-secret \
  --name hireedgeai/razorpay-credentials \
  --secret-string '{"key_id":"xxx","key_secret":"xxx"}'
```

Then reference in App Runner environment variables using:
```
OPENAI_API_KEY={{ secrets.hireedgeai/openai-api-key }}
```

### 5. Review and Deploy

- Review configuration
- Click **"Create & deploy"**
- Wait 5-10 minutes for deployment
- Get your service URL (e.g., `https://xxxxx.us-east-1.awsapprunner.com`)

## Required AWS Resources

### 1. ElastiCache Redis (for sessions)

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id hireedgeai-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --region us-east-1
```

**Cost**: ~$15/month (covered by AWS credits)

**Update code**: Modify `resume/services/session_manager.py` to use Redis

### 2. S3 Bucket (for file storage)

```bash
# Create S3 bucket
aws s3 mb s3://hireedgeai-files --region us-east-1

# Enable versioning (optional)
aws s3api put-bucket-versioning \
  --bucket hireedgeai-files \
  --versioning-configuration Status=Enabled
```

**Cost**: ~$1-5/month (Free Tier: 5GB free)

**Update code**: Modify file handlers to use S3 instead of local filesystem

### 3. Route 53 + Certificate Manager (for custom domain)

1. Create hosted zone in Route 53
2. Request SSL certificate in ACM
3. Configure custom domain in App Runner settings
4. Update DNS records

**Cost**: ~$1/month (hosted zone) + Free SSL

## Environment Variables Reference

| Variable | Required | Description | Source |
|----------|----------|-------------|--------|
| `HOST` | Yes | Server host | `0.0.0.0` |
| `PORT` | Yes | Server port | `8000` |
| `DEBUG` | Yes | Debug mode | `false` (production) |
| `FRONTEND_URL` | Yes | Frontend domain | Your React app URL |
| `OPENAI_API_KEY` | Yes | OpenAI API key | Secrets Manager |
| `OPENAI_MODEL` | Yes | OpenAI model | `gpt-4o-mini` |
| `RAZORPAY_KEY_ID` | Yes | Razorpay key | Secrets Manager |
| `RAZORPAY_KEY_SECRET` | Yes | Razorpay secret | Secrets Manager |
| `SESSION_EXPIRY_HOURS` | No | Session expiry | `24` (default) |

## Cost Estimation (with AWS Credits)

### First 12 Months (with AWS Activate):
- **App Runner**: $30-50/month → **$0** (covered by credits)
- **ElastiCache Redis**: $15/month → **$0** (covered by credits)
- **S3**: $1/month → **$0** (Free Tier)
- **Secrets Manager**: $2/month → **$0** (covered by credits)
- **Route 53**: $1/month → **$1/month**
- **Total**: **~$0-50/month** (mostly free with credits)

### After Credits Expire:
- **Total**: **~$50-90/month**

## Testing Deployment

```bash
# Get App Runner service URL
APP_URL="https://xxxxx.us-east-1.awsapprunner.com"

# Test health endpoint
curl $APP_URL/api/health

# Test resume endpoint (create session)
curl -X POST $APP_URL/api/resume/session/create \
  -H "Content-Type: application/json"
```

## CI/CD (Optional)

For automatic deployments on git push:

1. **GitHub Actions**: Push to ECR → Update App Runner
2. **AWS CodePipeline**: Full CI/CD pipeline
3. **App Runner Auto-deploy**: Enable automatic deployment in App Runner settings

## Monitoring

- **CloudWatch Logs**: Automatic log collection
- **CloudWatch Metrics**: CPU, Memory, Request count
- **Health Checks**: Automatic monitoring via `/api/health`

## Troubleshooting

### Deployment Fails
- Check CloudWatch logs
- Verify environment variables
- Check ECR image exists
- Verify health check endpoint

### High Costs
- Check CloudWatch metrics for resource usage
- Adjust instance size if needed
- Review auto-scaling settings

### Session Issues
- Ensure Redis is configured and accessible
- Check security groups allow connection
- Verify Redis endpoint in code

## Next Steps

1. ✅ Deploy to App Runner
2. ⚠️ Set up Redis (ElastiCache) - **Required for production**
3. ⚠️ Migrate file storage to S3 - **Required for production**
4. ✅ Configure custom domain
5. ✅ Set up monitoring alerts
6. ✅ Test all endpoints

## Migration Path

When you outgrow App Runner:
- **ECS Fargate**: More control, similar cost
- **EKS**: Only if you need advanced features
- App Runner can scale to 100+ instances, so may never need to migrate

