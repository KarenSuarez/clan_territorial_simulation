# clan_territorial_simulation/utils/logger.py
import logging
import os
from datetime import datetime

LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILENAME = os.path.join(LOG_DIR, f'simulation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')

file_handler = logging.FileHandler(LOG_FILENAME)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

def log_info(message):
    logger.info(message)

def log_debug(message):
    logger.debug(message)

def log_warning(message):
    logger.warning(message)

def log_error(message):
    logger.error(message)

def log_exception(message, exc_info=True):
    logger.exception(message, exc_info=exc_info)