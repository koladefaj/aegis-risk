from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    from aegis_shared.utils.logging import get_logger
    logger = get_logger("sqlalchemy")
    from aegis_shared.utils.tracing import get_correlation_id

    logger.info(
        "sql_query",
        statement=statement,
        parameters=parameters,
        correlation_id=get_correlation_id()
    )