from sqlalchemy import event
from sqlalchemy.engine import Engine
import time


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    from aegis_shared.utils.logging import get_logger
    from aegis_shared.utils.tracing import get_correlation_id

    logger = get_logger("sqlalchemy")
    # Store start time in connection info for later use
    conn.info.setdefault('query_start_time', []).append(time.time())
    
    logger.info(
        "sql_query_start",
        statement=statement,
        parameters=parameters,
        correlation_id=get_correlation_id(),
        service="sqlalchemy"
    )


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    from aegis_shared.utils.logging import get_logger
    from aegis_shared.utils.tracing import get_correlation_id

    logger = get_logger("sqlalchemy")
    
    # Calculate duration
    total = time.time() - conn.info['query_start_time'].pop()
    
    # Get row count if available (works for SELECTs)
    row_count = cursor.rowcount if cursor.rowcount != -1 else None
    
    logger.info(
        "sql_query_end",
        statement=statement,
        parameters=parameters,
        duration_ms=round(total * 1000, 2),
        row_count=row_count,
        correlation_id=get_correlation_id(),
        service="sqlalchemy"
    )