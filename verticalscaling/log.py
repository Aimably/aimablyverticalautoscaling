import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_debug(message):
    logger.debug(message)

def log_info(message):
    logger.info(message)

def log_error(message):
    logger.error(message)

def log_exception(e):
    logger.exception(e)