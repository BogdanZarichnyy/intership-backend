import os
import sys
from loguru import logger
from app.core.log_context import request_id_var, current_user_id_var

def inject_context(record):
  record["extra"]["request_id"] = request_id_var.get()
  record["extra"]["user_id"] = current_user_id_var.get()
  return record

def setup_logger():
  os.makedirs("logs", exist_ok=True)

  logger.remove()

  logger.configure(patcher=inject_context)

  log_format = (
    "{time:YYYY-MM-DD HH:mm:ss} "
    "[{level}] "
    "request_id={extra[request_id]} "
    "user_id={extra[user_id]} "
    "{name}: {message}"
  )

  logger.add(
    sys.stdout,
    level="INFO",
    format=log_format,
    enqueue=True,
    backtrace=True,
    diagnose=True,
  )

  logger.add(
    "logs/app.log",
    level="INFO",
    format=log_format,
    rotation="5 MB",
    retention="10 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
  )

  return logger

logger = setup_logger()
