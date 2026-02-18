import os
import sys
from loguru import logger

def setup_logger():
  os.makedirs("logs", exist_ok=True)

  logger.remove()  # видаляє default handler

  # консоль
  logger.add(
    sys.stdout,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {name}: {message}",
    enqueue=True,
    backtrace=True,
    diagnose=True,
  )

  # файл з ротацією
  logger.add(
    "logs/app.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {name}: {message}",
    rotation="5 MB",
    retention="10 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
  )

  return logger

logger = setup_logger()
