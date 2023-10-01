import logging
import sys


LOGGER = logging.getLogger(__name__)


def configure():
    logging.basicConfig(
        format='[%(asctime)s %(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG,
        stream=sys.stderr)
