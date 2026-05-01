output "public_url" {
  description = "Public URL of the application"
  value       = "http://${aws_instance.app.public_ip}"
}

output "ec2_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.app.public_ip
}

output "dynamodb_jobs_table_arn" {
  description = "ARN of the DynamoDB jobs table"
  value       = aws_dynamodb_table.jobs.arn
}

output "dynamodb_users_table_arn" {
  description = "ARN of the DynamoDB users table"
  value       = aws_dynamodb_table.users.arn
}

output "sqs_standard_queue_url" {
  description = "URL of the standard SQS queue"
  value       = aws_sqs_queue.reports_standard.url
}

output "sqs_high_queue_url" {
  description = "URL of the high priority SQS queue"
  value       = aws_sqs_queue.reports_high.url
}
