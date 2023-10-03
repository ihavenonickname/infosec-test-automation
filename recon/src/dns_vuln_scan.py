import json
import aiomqtt

from helper import MQTT_HOST, MQTT_PORT, check_installed, run_program, ReconTopics
from log import LOGGER, extra


async def scan_dns_vulnerabilities(domain: str, trace_id: str):
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


async def run_main_loop():
    LOGGER.debug('Checking if tools are installed')

    if not await check_installed('zonemaster-cli'):
        LOGGER.critical('Some tools are not installed')
        return

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        async with client.messages() as messages:
            await client.subscribe(ReconTopics.DNS_VULN_SCAN)
            async for message in messages:
                payload = json.loads(message.payload)
                trace_id = payload['trace_id']
                domain = payload['domain']
                await scan_dns_vulnerabilities(domain, trace_id)
