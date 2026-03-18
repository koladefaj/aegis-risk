# shared/aws/session_manager.py
import aioboto3
from typing import Optional
from aegis_shared.utils.logging import get_logger

logger = get_logger("boto_session")

_boto_session: aioboto3.Session | None = None

async def init_boto_session(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    region_name: str,
) -> None:
    """
    Initialize the aioboto3 session at service startup.
    """
    global _boto_session
    if _boto_session is None:
        _boto_session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        logger.info("Boto3 session initialized")


def get_boto_session() -> aioboto3.Session:
    if _boto_session is None:
        logger.error("Boto session not initialized")
        raise RuntimeError("Boto session not initialized")
    return _boto_session