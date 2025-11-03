# Terraform configuration for deploying Hierarchical Agent API to GCP Cloud Run

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "cloud_run_api" {
  service = "run.googleapis.com"
}

resource "google_project_service" "container_registry_api" {
  service = "containerregistry.googleapis.com"
}

resource "google_project_service" "artifact_registry_api" {
  service = "artifactregistry.googleapis.com"
}

# Create Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "hierarchical_agent_repo" {
  location      = var.region
  repository_id = var.repository_name
  description   = "Docker repository for Hierarchical Agent API"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry_api]
}

# Secret Manager for API keys
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_api_key" {
  secret_id = "google-api-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "groq_api_key" {
  secret_id = "groq-api-key"
  
  replication {
    auto {}
  }
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_service_account" {
  account_id   = "hierarchical-agent-sa"
  display_name = "Hierarchical Agent Cloud Run Service Account"
  description  = "Service account for Hierarchical Agent API Cloud Run service"
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "openai_secret_access" {
  secret_id = google_secret_manager_secret.openai_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

resource "google_secret_manager_secret_iam_member" "anthropic_secret_access" {
  secret_id = google_secret_manager_secret.anthropic_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

resource "google_secret_manager_secret_iam_member" "google_secret_access" {
  secret_id = google_secret_manager_secret.google_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

resource "google_secret_manager_secret_iam_member" "groq_secret_access" {
  secret_id = google_secret_manager_secret.groq_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "hierarchical_agent_api" {
  name     = var.service_name
  location = var.region
  
  template {
    service_account = google_service_account.cloud_run_service_account.email
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name}/${var.image_name}:${var.image_tag}"
      
      ports {
        container_port = 8000
      }
      
      env {
        name  = "API_HOST"
        value = "0.0.0.0"
      }
      
      env {
        name  = "API_PORT"
        value = "8000"
      }
      
      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }
      
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "GOOGLE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "GROQ_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.groq_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        
        cpu_idle = var.cpu_idle
      }
      
      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 10
        timeout_seconds       = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 30
        timeout_seconds       = 5
        period_seconds        = 30
        failure_threshold     = 3
      }
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
  
  depends_on = [
    google_project_service.cloud_run_api,
    google_artifact_registry_repository.hierarchical_agent_repo
  ]
}

# IAM policy for public access (optional - remove for private access)
resource "google_cloud_run_service_iam_member" "public_access" {
  count = var.allow_public_access ? 1 : 0
  
  service  = google_cloud_run_v2_service.hierarchical_agent_api.name
  location = google_cloud_run_v2_service.hierarchical_agent_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Custom domain mapping (optional)
resource "google_cloud_run_domain_mapping" "custom_domain" {
  count = var.custom_domain != "" ? 1 : 0
  
  location = var.region
  name     = var.custom_domain
  
  metadata {
    namespace = var.project_id
  }
  
  spec {
    route_name = google_cloud_run_v2_service.hierarchical_agent_api.name
  }
}