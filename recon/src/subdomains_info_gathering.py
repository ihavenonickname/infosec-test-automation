import json
from typing import NamedTuple

import asyncio_mqtt as aiomqtt

from helper import MQTT_HOST, MQTT_PORT, check_installed, run_program, ReconTopics
from log import LOGGER


class ProbeResultItem(NamedTuple):
    input_domain: str
    url: str
    status_code: int
    cnames: list
    techs: list


async def probe(domains: list) -> list:
    LOGGER.info('Investigating a batch of %d subdomains', len(domains))

    args = ['httpx-toolkit', '-sc', '-td', '-json', '-probe']

    httpx_result = await run_program(*args, stdin_lines=domains)

    for line in httpx_result:
        LOGGER.debug('httpx raw result: %s', line)

        serialized_line: dict = json.loads(line)
        subdomain = serialized_line['input']

        if serialized_line['failed']:
            LOGGER.info('%s is unresponsive', subdomain)
            continue

        item = ProbeResultItem(
            input_domain=subdomain,
            cnames=serialized_line.get('cnames'),
            url=serialized_line.get('url'),
            status_code=serialized_line.get('status-code'),
            techs=serialized_line.get('technologies'))

        LOGGER.info('%s is responsive', item.input_domain)
        LOGGER.info('%s replied %s',
                    item.input_domain, item.status_code)
        LOGGER.info('%s has full url %s',
                    item.input_domain, item.url)
        LOGGER.info('%s has canmes %s',
                    item.input_domain, item.cnames)
        LOGGER.info('%s has uses tech %s',
                    item.input_domain, item.techs)

    LOGGER.info('Done')


async def run_main_loop():
    LOGGER.debug('Checking if tools are installed')

    if not await check_installed('httpx-toolkit'):
        LOGGER.critical('Some tools are not installed')
        return

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        async with client.messages() as messages:
            await client.subscribe(ReconTopics.SUBDOMAINS_INFO_GATHERING)
            async for message in messages:
                LOGGER.debug('Got message from topic %s', message.topic)
                subdomains = message.payload.decode().splitlines()
                await probe(subdomains)
