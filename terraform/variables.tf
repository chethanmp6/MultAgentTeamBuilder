# Variables for GCP Cloud Run deployment

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "hierarchical-agent-api"
}

variable "repository_name" {
  description = "Name of the Artifact Registry repository"
  type        = string
  default     = "hierarchical-agent-repo"
}

variable "image_name" {
  description = "Name of the Docker image"
  type        = string
  default     = "hierarchical-agent-api"
}

variable "image_tag" {
  description = "Tag of the Docker image to deploy"
  type        = string
  default     = "latest"
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for each instance"
  type        = string
  default     = "2"
}

variable "memory_limit" {
  description = "Memory limit for each instance"
  type        = string
  default     = "4Gi"
}

variable "cpu_idle" {
  description = "Whether CPU should be throttled when idle"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Log level for the application"
  type        = string
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR."
  }
}

variable "allow_public_access" {
  description = "Whether to allow public access to the Cloud Run service"
  type        = bool
  default     = true
}

variable "custom_domain" {
  description = "Custom domain for the Cloud Run service (optional)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default = {
    application = "hierarchical-agent-api"
    managed-by  = "terraform"
  }
}