#!/bin/bash
set -e

echo "Initializing LocalStack resources..."

ENDPOINT="http://localhost:4566"
REGION="us-east-1"

# Create jobs table with GSI
awslocal dynamodb create-table \
  --table-name jobs \
  --attribute-definitions \
    AttributeName=job_id,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema AttributeName=job_id,KeyType=HASH \
  --global-secondary-indexes \
    '[{"IndexName":"user-jobs-index","KeySchema":[{"AttributeName":"user_id","KeyType":"HASH"},{"AttributeName":"created_at","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":5,"WriteCapacityUnits":5}}]' \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region $REGION

# Create users table with GSI
awslocal dynamodb create-table \
  --table-name users \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=username,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH \
  --global-secondary-indexes \
    '[{"IndexName":"username-index","KeySchema":[{"AttributeName":"username","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":5,"WriteCapacityUnits":5}}]' \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region $REGION

# Create SQS queues - DLQs first
awslocal sqs create-queue --queue-name reports-dlq-standard --region $REGION
awslocal sqs create-queue --queue-name reports-dlq-high --region $REGION

# Create main queues with DLQ redrive policy
awslocal sqs create-queue \
  --queue-name reports-queue-standard \
  --attributes '{
    "VisibilityTimeout":"30",
    "MessageRetentionPeriod":"345600",
    "RedrivePolicy":"{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:000000000000:reports-dlq-standard\",\"maxReceiveCount\":\"3\"}"
  }' \
  --region $REGION

awslocal sqs create-queue \
  --queue-name reports-queue-high \
  --attributes '{
    "VisibilityTimeout":"30",
    "MessageRetentionPeriod":"345600",
    "RedrivePolicy":"{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:000000000000:reports-dlq-high\",\"maxReceiveCount\":\"3\"}"
  }' \
  --region $REGION

echo "LocalStack initialization complete!"
echo "Tables: jobs, users"
echo "Queues: reports-queue-standard, reports-queue-high, reports-dlq-standard, reports-dlq-high"
