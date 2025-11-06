import logging
from typing import Any, Dict

def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger

def log_operation(logger: logging.Logger, message: str, extra: Dict[str, Any] | None = None):
    if extra is None:
        extra = {}
    logger.info(message + " | " + "; ".join(f"{k}={v}" for k,v in extra.items()))
