# Infra/modules/lambda_monitor/outputs.tf


output "lambda_function_name" {
  value = aws_lambda_function.monitor.function_name
}

output "ecr_repo_url" {
  value = aws_ecr_repository.monitor.repository_url
}
