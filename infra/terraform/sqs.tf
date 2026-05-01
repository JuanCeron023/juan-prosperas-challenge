# Standard DLQ
resource "aws_sqs_queue" "reports_dlq_standard" {
  name                       = "${var.project_name}-reports-dlq-standard"
  message_retention_seconds  = 1209600  # 14 days
  visibility_timeout_seconds = 30

  tags = {
    Project = var.project_name
  }
}

# High priority DLQ
resource "aws_sqs_queue" "reports_dlq_high" {
  name                       = "${var.project_name}-reports-dlq-high"
  message_retention_seconds  = 1209600  # 14 days
  visibility_timeout_seconds = 30

  tags = {
    Project = var.project_name
  }
}

# Standard queue
resource "aws_sqs_queue" "reports_standard" {
  name                       = "${var.project_name}-reports-queue-standard"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600  # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.reports_dlq_standard.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project = var.project_name
  }
}

# High priority queue
resource "aws_sqs_queue" "reports_high" {
  name                       = "${var.project_name}-reports-queue-high"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600  # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.reports_dlq_high.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project = var.project_name
  }
}
