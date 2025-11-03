# Outputs for GCP Cloud Run deployment

output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.hierarchical_agent_api.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.hierarchical_agent_api.name
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_v2_service.hierarchical_agent_api.location
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = google_artifact_registry_repository.hierarchical_agent_repo.name
}

output "docker_image_url" {
  description = "Full Docker image URL for pushing"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name}/${var.image_name}"
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.cloud_run_service_account.email
}

output "secret_manager_secrets" {
  description = "List of Secret Manager secret IDs created"
  value = [
    google_secret_manager_secret.openai_api_key.secret_id,
    google_secret_manager_secret.anthropic_api_key.secret_id,
    google_secret_manager_secret.google_api_key.secret_id,
    google_secret_manager_secret.groq_api_key.secret_id
  ]
}

output "api_docs_url" {
  description = "URL to the API documentation"
  value       = "${google_cloud_run_v2_service.hierarchical_agent_api.uri}/docs"
}

output "health_check_url" {
  description = "URL for health checks"
  value       = "${google_cloud_run_v2_service.hierarchical_agent_api.uri}/health"
}

output "custom_domain_url" {
  description = "Custom domain URL (if configured)"
  value       = var.custom_domain != "" ? "https://${var.custom_domain}" : null
}

output "deployment_commands" {
  description = "Commands to build and deploy the Docker image"
  value = {
    configure_docker = "gcloud auth configure-docker ${var.region}-docker.pkg.dev"
    build_image     = "docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name}/${var.image_name}:${var.image_tag} ."
    push_image      = "docker push ${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_name}/${var.image_name}:${var.image_tag}"
    update_service  = "terraform apply -var='image_tag=${var.image_tag}'"
  }
}