import json

import aiomqtt

from helper import run_program
from custom_logger import LOGGER, extra
from messaging_abstractions import handle


@handle('recon/subdomains-info-gathering')
async def handler(payload: dict, client: aiomqtt.Client):
    trace_id = payload['trace_id']
    domains = payload['subdomains']

    LOGGER.info('Starting information gathering', extra=extra(trace_id))

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

    LOGGER.info('Finished information gathering', extra=extra(trace_id))
