"""gRPC interceptors for logging and authentication."""

import time
import uuid
import grpc
from grpc import HandlerCallDetails, RpcMethodHandler
from grpc.aio import ServerInterceptor

from aegis_shared.utils.logging import get_logger
from aegis_shared.utils.tracing import set_correlation_id, clear_correlation_id

logger = get_logger("transaction_service_grpc_interceptor")


class LoggingInterceptor(ServerInterceptor):
    """gRPC server interceptor that logs all incoming requests with timing and propagates correlation IDs."""

    async def intercept_service(
        self,
        continuation,
        handler_call_details: HandlerCallDetails,
    ) -> RpcMethodHandler:

        handler = await continuation(handler_call_details)
        if handler is None:
            return handler

        method = handler_call_details.method

        # Determine which type of RPC handler we have
        if handler.unary_unary:
            original_fn = handler.unary_unary
            def make_new_handler(fn): 
                return handler._replace(unary_unary=fn)
        elif handler.unary_stream:
            original_fn = handler.unary_stream
            def make_new_handler(fn):
                return handler._replace(unary_stream=fn)
        elif handler.stream_unary:
            original_fn = handler.stream_unary
            def make_new_handler(fn):
                return handler._replace(stream_unary=fn)
        elif handler.stream_stream:
            original_fn = handler.stream_stream
            def make_new_handler(fn):
                return handler._replace(stream_stream=fn)
        else:
            return handler

        async def wrapper(request, context):

            start_time = time.perf_counter()

            # Extract correlation ID from metadata or generate a new one
            metadata = {k.lower(): v for k, v in context.invocation_metadata()}
            correlation_id = metadata.get("x-correlation-id")
            if not correlation_id:
                # fallback: generate new ID
                correlation_id = str(uuid.uuid4())
            set_correlation_id(correlation_id)  # bind to context for logging everywhere

            # Send correlation ID back to client
            await context.send_initial_metadata((("x-correlation-id", correlation_id),))

            logger.info(
                "grpc_request_started",
                method=method,
                correlation_id=correlation_id,
            )

            try:
                response = await original_fn(request, context)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    "grpc_request_completed",
                    method=method,
                    duration_ms=round(elapsed_ms, 2),
                    correlation_id=correlation_id,
                )
                return response

            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                current_code = context.code()

                if current_code is None or current_code == grpc.StatusCode.OK:
                    context.set_code(grpc.StatusCode.INTERNAL)
                    context.set_details(str(e))  # only raw crashes
                    log_fn = logger.error
                else:
                    log_fn = logger.warning

                log_fn(
                    "grpc_request_failed",
                    method=method,
                    duration_ms=round(elapsed_ms, 2),
                    error=str(e),
                    status_code=str(current_code),
                    correlation_id=correlation_id,
                )
                raise

            finally:
                clear_correlation_id()  # remove from context

        return make_new_handler(wrapper)