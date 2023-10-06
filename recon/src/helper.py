import asyncio
from datetime import datetime

from custom_logger import LOGGER, extra


_SEMAPHORE = asyncio.Semaphore(15)


async def run_program(program: str,
                      *args: str,
                      trace_id: str,
                      stdin_lines: list[str] | None = None) -> list[str]:
    LOGGER.debug(
        'Starting program execution',
        extra=extra(trace_id, program=program, args=args))

    stdin_bytes = bytes()

    if stdin_lines:
        stdin_bytes = '\n'.join(stdin_lines).encode('utf8')

    start = datetime.utcnow()

    async with _SEMAPHORE:
        process = await asyncio.create_subprocess_exec(
            program,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE, )

        process_stdout, _ = await process.communicate(stdin_bytes)

    elapsed = datetime.utcnow() - start

    LOGGER.debug(
        'Program execution ended',
        extra=extra(
            trace_id,
            program=program,
            return_code=process.returncode,
            elapsed_seconds=round(elapsed.total_seconds(), 2)))

    return [
        line.strip() for line
        in process_stdout.decode('utf8').strip().splitlines()
    ]


def extract_trace_id(payload: dict[str, object]) -> str:
    if 'trace_id' not in payload:
        raise Exception('trace_id not found in payload')

    if type(payload['trace_id']) != str:
        raise Exception('trace_id must be str')

    return payload['trace_id']
