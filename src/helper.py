import subprocess
from datetime import datetime

from log import LOGGER


def run_shell_command(*args):
    LOGGER.debug('Running command %s', args)

    start = datetime.utcnow()

    execution_result = subprocess.run(args, capture_output=True)

    elapsed = datetime.utcnow() - start

    LOGGER.debug('Return code is %d', execution_result.returncode)
    LOGGER.debug('Elapsed %.1f seconds', elapsed.total_seconds())

    return execution_result.stdout.decode('utf8')
