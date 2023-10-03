import json

import aiomqtt

from helper import MQTT_HOST, MQTT_PORT, check_installed, run_program, ReconTopics
from log import LOGGER, extra


async def probe(domains: list, trace_id: str):
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

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        async with client.messages() as messages:
            await client.subscribe(ReconTopics.SUBDOMAINS_INFO_GATHERING)
            async for message in messages:
                payload = json.loads(message.payload)
                trace_id = payload['trace_id']
                subdomains = payload['subdomains']

                await probe(subdomains, trace_id)
