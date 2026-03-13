"""SQS message publisher for transaction events."""

import json
import asyncio
import aioboto3
from typing import Optional
from app.config import settings
from aegis_shared.utils.logging import get_logger

logger = get_logger("sqs_publisher")


class SQSPublisher:
    """Publishes transaction events to AWS SQS.

    Supports async publishing with retry/backoff.
    """

    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self):
        self.session = aioboto3.Session()
        self._queue_url: str | None = None

    def _client(self):
        """Return a configured async SQS client context manager."""
        return self.session.client(
            "sqs",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_ENDPOINT_URL,
        )

    async def _get_queue_url(self) -> str:
        """Resolve and cache the SQS queue URL from the queue name."""
        if self._queue_url:
            return self._queue_url

        try:
            async with self._client() as client:
                response = await client.get_queue_url(
                    QueueName=settings.SQS_TRANSACTION_QUEUE
                )
                self._queue_url = response["QueueUrl"]
                return self._queue_url
            
        except Exception as e:
            logger.warning("sqs_queue_url_resolution_failed", error=str(e))

            if settings.AWS_ENDPOINT_URL:
                fallback = (
                    f"{settings.AWS_ENDPOINT_URL}/000000000000/"
                    f"{settings.SQS_TRANSACTION_QUEUE}"
                )

                self._queue_url = fallback

                return fallback
            raise RuntimeError("Failed to resolve SQS queue URL") from e

    async def publish_transaction_queued(self, payload: dict) -> Optional[str]:
        """Publish a TransactionQueued event to SQS with retries.

        Args:
            payload: Transaction event data (must contain 'transaction_id').

        Returns:
            SQS MessageId on success, None on failure.
        """

        transaction_id = payload.get("transaction_id")

        if not transaction_id:
            logger.warning("missing_transaction_id_in_payload", payload=payload)
            raise ValueError("transaction_id is required in payload")

        queue_url = await self._get_queue_url()
        is_fifo = queue_url.endswith(".fifo")

        for attempt in range(1, self.RETRY_ATTEMPTS + 1):
            try:
                async with self._client() as client:
                    # build kwargs dict only add FIFO params if needed
                    send_kwargs = {
                        "QueueUrl": queue_url,
                        "MessageBody": json.dumps(payload, default=str),
                        "MessageAttributes": {
                            "EventType": {
                                "DataType": "String",
                                "StringValue": "TransactionQueued",
                            },
                            "TransactionId": {
                                "DataType": "String",
                                "StringValue": str(transaction_id),
                            },
                        },
                    }

                    if is_fifo:
                        send_kwargs["MessageGroupId"] = str(transaction_id)
                        send_kwargs["MessageDeduplicationId"] = str(transaction_id)

                    response = await client.send_message(**send_kwargs)

                message_id = response.get("MessageId")
                logger.info(
                    "sqs_message_published",
                    message_id=message_id,
                    transaction_id=transaction_id,
                    queue=settings.SQS_TRANSACTION_QUEUE,
                    attempt=attempt,
                )
                return message_id

            except Exception as e:
                logger.error(
                    "sqs_publish_attempt_failed",
                    attempt=attempt,
                    error=str(e),
                    transaction_id=transaction_id,
                )
                if attempt < self.RETRY_ATTEMPTS:
                    await asyncio.sleep(self.RETRY_DELAY * attempt)
                else:
                    raise RuntimeError(
                        f"Failed to publish transaction {transaction_id} to SQS"
                    ) from e