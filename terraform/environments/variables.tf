# variables.tf - defines all the input variables my terraform config needs

variable "azure_region" {
  description = "Azure region"
  type        = string
  default     = "uksouth" # also London
}

variable "azure_subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  # no default - i have to pass this in via tfvars
}

variable "project_name" {
  description = "Project name used for naming all my resources"
  type        = string
  default     = "palm"
}

variable "environment" {
  description = "Which environment i'm deploying to"
  type        = string
  default     = "prod"
}

variable "backend_api_url" {
  description = "Full URL the dashboard calls for sensor events, e.g. https://<backend-host>/events/latest"
  type        = string
}
