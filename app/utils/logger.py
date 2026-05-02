import sys
from loguru import logger

def get_logger(name: str):
    logger.remove() # Remove default handler
    
    logger.add(
        sys.stderr,
        format=(
            '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | '
            '<level>{level: <8}</level> | '
            '<cyan>{extra[module]}</cyan> - <level>{message}</level>'
        ),
        level='DEBUG',
        colorize=True
    )
    
    logger.add(
        'data/logs/app.log',
        rotation='10 MB',
        retention='7 days',
        compression='zip',
        format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} - {message}',
        level='INFO',
        enqueue=True
    )
    
    return logger.bind(model=name)