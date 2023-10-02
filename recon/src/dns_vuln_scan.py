import asyncio_mqtt as aiomqtt

from helper import MQTT_HOST, MQTT_PORT, check_installed, run_program, ReconTopics
from log import LOGGER


async def scan_dns_vulnerabilities(domain: str):
    LOGGER.info('Investigating domain %s', domain)

    args = ['zonemaster-cli', '--no-progress', '--no-count',
            '--no-time', '--level', 'WARNING', domain]

    zonemaster_result = await run_program(*args)

    if len(zonemaster_result) > 2:
        for line in zonemaster_result[2:]:
            i = line.index(' ')
            level, message = line[:i], line[i:].strip()
            LOGGER.info('Vulnerability of level %s: %s', level, message)

    LOGGER.info('Done with %s', domain)


async def run_main_loop():
    LOGGER.debug('Checking if tools are installed')

    if not await check_installed('zonemaster-cli'):
        LOGGER.critical('Some tools are not installed')
        return

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        async with client.messages() as messages:
            await client.subscribe(ReconTopics.DNS_VULN_SCAN)
            async for message in messages:
                LOGGER.debug('Got message from topic %s', message.topic)
                subdomains = message.payload.decode()
                await scan_dns_vulnerabilities(subdomains)
