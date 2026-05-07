variable "project_name" {
  description = "Project name used in AWS resource naming."
  type        = string
  default     = "data-platform"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Owner tag applied to all managed resources."
  type        = string
  default     = "data-engineering"
}

variable "aws_region" {
  description = "AWS region for the deployment."
  type        = string
  default     = "us-east-1"
}

variable "artifact_path" {
  description = "Path to the packaged runtime artifact produced by make package."
  type        = string
  default     = "../artifacts/data_platform_bundle.zip"
}

variable "artifact_bucket_suffix" {
  description = "Suffix appended to the generated artifact bucket name."
  type        = string
  default     = "artifacts"
}

variable "artifact_bucket_force_destroy" {
  description = "Whether Terraform may destroy the artifact bucket even when it contains objects. Keep true for dev and sandbox environments."
  type        = bool
  default     = true
}

variable "enable_artifact_bucket_versioning" {
  description = "Whether to enable versioning on the artifact bucket. Defaults to false to keep dev environments cheap and easy to destroy."
  type        = bool
  default     = false
}

variable "execution_role_name" {
  description = "IAM role name for AWS data jobs."
  type        = string
  default     = "data-job-execution-role"
}

variable "tags" {
  description = "Additional tags applied to all resources."
  type        = map(string)
  default     = {}
}
