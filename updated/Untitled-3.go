#Infra/modules/lambda_monitor/variables.tf

variable "environment" {
  description = "uat or prod"
  type        = string
  default     = "uat"
}

variable "function_name" {
  type = string
}

variable "ecr_repo_name" {
  type = string
}

variable "image_tag" {
  type = string
  default = "monitorlambda"
}

variable "s3_bucket" {
  type = string
}

variable "secret_name" {
  type = string
  default = "azneprod"
}

variable "email_source" {
  type = string
  default = "alerts@theaa.com"
}

variable "email_recipient" {
  type = string
  default = "ROAD_Ops_L2_Support@theaa.com"
}

variable "aws_region" {
  type = string
  default = "eu-west-1"
}

variable "create_role" {
  type    = bool
  default = true
}

variable "role_arn" {
  type    = string
  default = ""
}
