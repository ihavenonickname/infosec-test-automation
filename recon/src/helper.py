import asyncio
import os
from datetime import datetime
from typing import NamedTuple

from log import LOGGER, extra


_SEMAPHORE = asyncio.Semaphore(15)

MQTT_HOST = os.environ['MQTT_HOST']
MQTT_PORT = int(os.environ['MQTT_PORT'])


class ReconTopics(NamedTuple):
    START = 'recon/start'
    SUBDOMAIN_ENUMERATION = 'recon/subdomain-enumeration'
    DNS_VULN_SCAN = 'recon/dns-vuln-scan'
    SUBDOMAINS_INFO_GATHERING = 'recon/subdomains-info-gathering'
    PORT_SCANNING = 'recon/port-scanning'


async def run_program(program: str,
                      *args: str,
                      stdin_lines: list[str] | None = None,
                      trace_id: str | None = None) -> list[str]:
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

    process_stdout = [
        line.strip() for line
        in process_stdout.decode('utf8').strip().splitlines()
    ]

    return process_stdout


async def check_installed(*programs: str) -> bool:
    for program in programs:
        try:
            await run_program(program)
            LOGGER.debug(f'{program} is installed')
        except FileNotFoundError:
            LOGGER.error(f'{program} is not installed')
            return False
        except Exception:
            LOGGER.exception(
                'Unexpected exception while checking if program is installed')
            return False

    return True
