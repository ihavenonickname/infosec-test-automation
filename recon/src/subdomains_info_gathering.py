import json

import aiomqtt

from helper import check_installed, loop_forever, run_program, ReconTopics
from log import LOGGER, extra


async def msg_handler(payload: dict, client: aiomqtt.Client):
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


async def run_main_loop():
    LOGGER.debug('Checking if tools are installed')

    if not await check_installed('httpx-toolkit'):
        LOGGER.critical('Some tools are not installed')
        return

    await loop_forever(
        topic_name=ReconTopics.SUBDOMAINS_INFO_GATHERING,
        step_name='subdomains-info-gathering',
        msg_handler=msg_handler)
