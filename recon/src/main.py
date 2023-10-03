import asyncio
import json
import uuid

import aiomqtt

from helper import MQTT_HOST, MQTT_PORT, ReconTopics
from log import LOGGER, configure_log, extra
import subdomains_info_gathering
import subdomain_enumeration
import dns_vuln_scan


async def main():
    configure_log()

    LOGGER.debug('MQTT_HOST: %s', MQTT_HOST)
    LOGGER.debug('MQTT_PORT: %d', MQTT_PORT)

    asyncio.create_task(subdomain_enumeration.run_main_loop())
    asyncio.create_task(subdomains_info_gathering.run_main_loop())
    asyncio.create_task(dns_vuln_scan.run_main_loop())

    LOGGER.debug('Starting main run')

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        async with client.messages() as messages:
            await client.subscribe(ReconTopics.START)
            async for message in messages:
                trace_id = str(uuid.uuid4())

                LOGGER.debug(
                    'Got message from topic %s',
                    message.topic,
                    extra=extra(trace_id))

                payload = json.dumps({
                    'trace_id': trace_id,
                    'domain': message.payload.decode(),
                })

                await client.publish(ReconTopics.SUBDOMAIN_ENUMERATION, payload)
                await client.publish(ReconTopics.DNS_VULN_SCAN, payload)

if __name__ == '__main__':
    asyncio.run(main())
