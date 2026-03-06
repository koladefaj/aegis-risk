#!/bin/bash
set -e

echo "Creating SQS queues in LocalStack..."

# Dead Letter Queues first
awslocal sqs create-queue --queue-name aegis-transactions-dlq
awslocal sqs create-queue --queue-name aegis-risk-completed-dlq

# Get DLQ ARNs
TRANSACTION_DLQ_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/aegis-transactions-dlq \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

RISK_DLQ_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/aegis-risk-completed-dlq \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

# Main queues with DLQ redrive policy
awslocal sqs create-queue --queue-name aegis-transactions \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"${TRANSACTION_DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}"

awslocal sqs create-queue --queue-name aegis-risk-completed \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"${RISK_DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}"

echo "SQS queues created successfully"
awslocal sqs list-queues
