from typing import cast
import aiomqtt

from helper import run_program, extract_trace_id
from custom_logger import LOGGER, extra
from messaging_abstractions import handle


@handle('recon/dns-scan/start')
async def handler(payload: dict[str, object], client: aiomqtt.Client) -> None:
    trace_id = extract_trace_id(payload)

    try:
        domain = cast(str, payload['domain'])
    except KeyError:
        LOGGER.exception('domain is required', extra=extra(trace_id))
        return

    LOGGER.info('Starting DNS scan', extra=extra(trace_id, domain=domain))

    zonemaster_result = await run_program(
        'zonemaster-cli',
        '--no-progress',
        '--no-count',
        '--no-time',
        '--level',
        'WARNING',
        domain,
        trace_id=trace_id)

    if len(zonemaster_result) > 2:
        for line in zonemaster_result[2:]:
            i = line.index(' ')
            level, message = line[:i], line[i:].strip()
            LOGGER.info(
                'Found DNS vulnerability',
                extra=extra(trace_id, level=level, message=message))

    LOGGER.info('Finished DNS scan', extra=extra(trace_id))
