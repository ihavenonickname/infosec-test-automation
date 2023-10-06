import json

import aiomqtt

from helper import run_program
from custom_logger import LOGGER, extra
from messaging_abstractions import handle


@handle('recon/webapp-scan')
async def handler(payload: dict, client: aiomqtt.Client):
    try:
        trace_id = payload['trace_id']
        domains = payload['hostnames']
    except KeyError:
        LOGGER.exception('Payload incomplete', extra=extra(trace_id))
        return

    LOGGER.info('Starting webapp scan', extra=extra(trace_id))

    httpx_result = await run_program(
        'httpx-toolkit',
        '-sc',
        '-td',
        '-json',
        '-probe',
        stdin_lines=domains,
        trace_id=trace_id)

    for line in httpx_result:
        LOGGER.debug('httpx raw line', extra=extra(trace_id, line=line))

        serialized_line: dict = json.loads(line)
        subdomain = serialized_line['input']

        if serialized_line['failed']:
            LOGGER.info(
                'Subdomain unresponsive',
                extra=extra(trace_id, subdomain=subdomain))
            continue

        LOGGER.info(
            'Found some info',
            extra=extra(
                trace_id,
                subdomain=subdomain,
                cnames=serialized_line.get('cnames'),
                url=serialized_line.get('url'),
                status_code=serialized_line.get('status-code'),
                techs=serialized_line.get('technologies')))

    LOGGER.info('Finished webapp scan', extra=extra(trace_id))
