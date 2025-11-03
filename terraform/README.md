# Terraform GCP Cloud Run Deployment

This Terraform configuration deploys the Hierarchical Agent API to Google Cloud Platform using Cloud Run.

## Prerequisites

1. **Google Cloud SDK**: Install and authenticate
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Terraform**: Install Terraform >= 1.0

3. **Docker**: For building and pushing images

4. **Enable APIs**: The following APIs will be enabled automatically:
   - Cloud Run API
   - Container Registry API
   - Artifact Registry API
   - Secret Manager API

## Setup

1. **Copy and configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your project ID and preferences
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Store API keys in Secret Manager** (after applying):
   ```bash
   # Store your API keys (replace with actual keys)
   echo -n "your-openai-key" | gcloud secrets versions add openai-api-key --data-file=-
   echo -n "your-anthropic-key" | gcloud secrets versions add anthropic-api-key --data-file=-
   echo -n "your-google-key" | gcloud secrets versions add google-api-key --data-file=-
   echo -n "your-groq-key" | gcloud secrets versions add groq-api-key --data-file=-
   ```

## Deployment

1. **Plan the deployment**:
   ```bash
   terraform plan
   ```

2. **Apply the configuration**:
   ```bash
   terraform apply
   ```

3. **Build and push Docker image**:
   ```bash
   # Configure Docker for Artifact Registry
   gcloud auth configure-docker us-central1-docker.pkg.dev
   
   # Build the image
   docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/hierarchical-agent-repo/hierarchical-agent-api:latest .
   
   # Push the image
   docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/hierarchical-agent-repo/hierarchical-agent-api:latest
   
   # Update the service (if needed)
   terraform apply
   ```

## Configuration Options

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_id` | GCP project ID | **Required** |
| `region` | Deployment region | `us-central1` |
| `service_name` | Cloud Run service name | `hierarchical-agent-api` |
| `min_instances` | Minimum instances | `0` |
| `max_instances` | Maximum instances | `10` |
| `cpu_limit` | CPU limit per instance | `2` |
| `memory_limit` | Memory limit per instance | `4Gi` |
| `allow_public_access` | Allow public access | `true` |
| `custom_domain` | Custom domain (optional) | `""` |

### Resources Created

- **Cloud Run Service**: Main API service
- **Artifact Registry**: Docker image repository
- **Secret Manager**: Secure storage for API keys
- **Service Account**: For Cloud Run with minimal permissions
- **IAM Bindings**: Access to secrets and public access (if enabled)

## Post-Deployment

After successful deployment, you'll get outputs including:

- **Service URL**: Direct URL to your API
- **API Docs**: URL to Swagger documentation (`/docs`)
- **Health Check**: URL for monitoring (`/health`)

## Updating the Service

To deploy a new version:

1. **Build new image with tag**:
   ```bash
   docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/hierarchical-agent-repo/hierarchical-agent-api:v1.1 .
   docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/hierarchical-agent-repo/hierarchical-agent-api:v1.1
   ```

2. **Update Terraform**:
   ```bash
   terraform apply -var='image_tag=v1.1'
   ```

## Security Notes

- API keys are stored securely in Secret Manager
- Service account follows principle of least privilege
- HTTPS is enforced by default
- Set `allow_public_access = false` for private deployments

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

## Troubleshooting

1. **Permission Issues**: Ensure your account has Cloud Run Admin, Artifact Registry Admin, and Secret Manager Admin roles
2. **Image Not Found**: Verify the image was pushed to Artifact Registry
3. **Secret Access**: Check that secrets contain valid API keys
4. **Health Check Failures**: Monitor Cloud Run logs for startup issues

## Cost Optimization

- Set `min_instances = 0` for development (cold starts)
- Adjust `cpu_limit` and `memory_limit` based on usage
- Use `cpu_idle = true` to reduce costs during low traffic
- Monitor usage and adjust `max_instances` accordingly