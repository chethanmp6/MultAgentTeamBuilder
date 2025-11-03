# Set variables
PROJECT_ID="psyched-span-468213-q4"
REGION="us-central1"
REPO_NAME="my-test-docker-repo"
IMAGE_NAME="my-test-app"
TAG="v1.0.0"

# Enable services
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository (if not exists)
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION

# Build and push in one command
gcloud builds submit \
    --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${TAG}