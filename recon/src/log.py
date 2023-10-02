import logging
import sys


LOGGER = logging.getLogger(__name__)


def configure_log():
    logging.basicConfig(
        format='[%(asctime)s] [%(levelname)s] [%(filename)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG,
        stream=sys.stderr)
