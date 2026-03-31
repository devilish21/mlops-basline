import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logger(name: str = "mlops-pipeline"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger()
