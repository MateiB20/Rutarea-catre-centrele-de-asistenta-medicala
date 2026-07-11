import logging
import os
logger = logging.getLogger(__name__)
logging.basicConfig(filename='debug_log.txt', level=logging.INFO)
log_file = os.path.join(os.path.dirname(__file__), "debug_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("LicentaApp")

def log_debug(message):
    logger.info("INFO "+str(message))

def log_error(message):
    logger.error("EROARE " + str(message))