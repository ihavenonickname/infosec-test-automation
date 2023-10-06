import json
from typing import cast

import aiomqtt

from helper import extract_trace_id, run_program
from custom_logger import LOGGER, extra
from messaging_abstractions import handle


@handle('recon/webapp-scan')
async def handler(payload: dict[str, object], client: aiomqtt.Client) -> None:
    trace_id = extract_trace_id(payload)

    try:
        hostnames = cast(list[str], payload['hostnames'])
    except KeyError:
        LOGGER.exception('hostnames is required', extra=extra(trace_id))
        return

    LOGGER.info('Starting webapp scan', extra=extra(trace_id))

    httpx_result = await run_program(
        'httpx-toolkit',
        '-sc',
        '-td',
        '-json',
        '-probe',
        stdin_lines=hostnames,
        trace_id=trace_id)

    for line in httpx_result:
        LOGGER.debug('httpx raw line', extra=extra(trace_id, line=line))

        serialized_line: dict[str, object] = json.loads(line)
        hostname = serialized_line['input']

        if serialized_line['failed']:
            LOGGER.info(
                'Hostname unresponsive',
                extra=extra(trace_id, hostname=hostname))
            continue

        LOGGER.info(
            'Found some info',
            extra=extra(
                trace_id,
                hostname=hostname,
                cnames=serialized_line.get('cnames'),
                url=serialized_line.get('url'),
                status_code=serialized_line.get('status-code'),
                techs=serialized_line.get('technologies')))

    LOGGER.info('Finished webapp scan', extra=extra(trace_id))
