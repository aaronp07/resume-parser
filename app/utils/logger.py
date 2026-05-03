import sys
from loguru import logger

def get_logger(name: str):
    logger.remove() # Remove default handler
    
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="INFO",
        enqueue=True
    )

    logger.add(
        "data/logs/app.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="INFO",
        enqueue=True
    )
    
    return logger.bind(model=name)