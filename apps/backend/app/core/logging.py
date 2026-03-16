import structlog


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
