import logging
import os

from rchat.conf import STORAGE_DIR, STORAGE_FOLDERS

logger = logging.getLogger(__name__)


def create_storage_folders():
    for folder in STORAGE_FOLDERS:
        path = os.path.join(STORAGE_DIR, folder)
        if not os.path.exists(path):
            logger.info("Create storage folder %s", folder)
            os.mkdir(path)
