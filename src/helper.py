import asyncio
import io
from datetime import datetime

from log import LOGGER


_SEMAPHORE = asyncio.Semaphore(15)


async def run_program(program, *args, stdin_lines=None) -> list[str]:
    LOGGER.debug('Running program: %s %s', program, args)

    if stdin_lines:
        stdin_lines = '\n'.join(stdin_lines).encode('utf8')

    start = datetime.utcnow()

    async with _SEMAPHORE:
        process = await asyncio.create_subprocess_exec(
            program,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE, )

        process_stdout, _ = await process.communicate(stdin_lines)

    elapsed = datetime.utcnow() - start

    LOGGER.debug(
        'Program %s returned %d after %.1f seconds', 
        program, 
        process.returncode, 
        elapsed.total_seconds())

    process_stdout = [
        line.strip() for line
        in process_stdout.decode('utf8').strip().splitlines()
    ]

    return process_stdout
