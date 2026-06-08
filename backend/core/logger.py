from loguru import logger
from core.config import settings
import sys

def setup_logging():
    logger.remove()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(sys.stderr, format=log_format, level="DEBUG" if settings.DEBUG else "INFO")
    logger.info(f"Đã khởi tạo logger. Môi trường = {settings.ENVIRONMENT}")
