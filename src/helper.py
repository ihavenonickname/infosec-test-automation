import subprocess
from datetime import datetime

from log import LOGGER


def run_shell_command(*args, input_lines=None) -> str:
    LOGGER.debug('Running command %s', args)

    start = datetime.utcnow()

    if input_lines:
        input_lines = '\n'.join(input_lines).encode('utf8')

    execution_result = subprocess.run(
        args,
        capture_output=True,
        input=input_lines)

    elapsed = datetime.utcnow() - start

    LOGGER.debug('Return code is %d', execution_result.returncode)
    LOGGER.debug('Elapsed %.1f seconds', elapsed.total_seconds())

    return execution_result.stdout.decode('utf8')
