"""Risk Engine Service — gRPC server + SQS worker entrypoint."""

import asyncio
from concurrent import futures

import grpc

import aegis_shared.generated.common_pb2  # noqa: F401

from app.engine.rules import get_all_rules
from app.engine.scorer import RiskScorer
from app.grpc_clients.ml_client import MLGRPCClient
from app.repositories.account_profile_repo import AccountProfileRepository
from app.repositories.risk_repo import RiskResultRepository
from app.config import settings
from app.engine.orchestrator import RiskOrchestrator
from app.grpc_server.servicer import RiskEngineServicer
from app.grpc_server.interceptors import LoggingInterceptor
from app.worker import RiskWorker
from app.db.session import engine
from aegis_shared.utils.logging import setup_logger
from aegis_shared.utils.sqs import init_boto_session
from aegis_shared.utils.redis import init_redis, close_redis
from aegis_shared.generated import risk_engine_pb2_grpc

logger = setup_logger("risk-engine-service", settings.LOG_LEVEL)


async def serve():
    """Start the Risk Engine gRPC server and SQS worker."""

    # init downstream clients and resources before starting server
    await init_boto_session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    await init_redis(settings.REDIS_URL)

    orchestrator = RiskOrchestrator(
        scorer=RiskScorer(),
        ml_client=MLGRPCClient(),
    )

    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[LoggingInterceptor()],
    )

    servicer = RiskEngineServicer(orchestrator)
    risk_engine_pb2_grpc.add_RiskEngineServiceServicer_to_server(servicer, server)

    listen_addr = f"0.0.0.0:{settings.RISK_ENGINE_GRPC_PORT}"
    server.add_insecure_port(listen_addr)

    logger.info("risk_engine_service_starting", address=listen_addr)
    await server.start()
    logger.info("risk_engine_service_started", address=listen_addr)

    # Start SQS worker alongside gRPC server
    shutdown_event = asyncio.Event()
    worker = RiskWorker(orchestrator)

    try:
        # Run gRPC server and SQS worker concurrently
        await asyncio.gather(
            server.wait_for_termination(),
            worker.run(shutdown_event),
        )
    except KeyboardInterrupt:
        logger.info("risk_engine_service_keyboard_interrupt_received")
    finally:
        logger.info("risk_engine_service_shutting_down")
        shutdown_event.set()                # signal worker to stop
        await server.stop(grace=5)          # finish in-flight RPCs
        await engine.dispose()              # close DB connection pool
        await close_redis()                 # close Redis pool
        logger.info("risk_engine_service_stopped")


if __name__ == "__main__":
    asyncio.run(serve())