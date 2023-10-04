import asyncio
import json
import signal
import uuid

import aiomqtt

from helper import MQTT_HOST, MQTT_PORT, ReconTopics
from log import LOGGER, configure_log, extra
import subdomains_info_gathering
import subdomain_enumeration
import dns_vuln_scan


async def watch_start_messages():
    LOGGER.debug('Starting main run')

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        async with client.messages() as messages:
            await client.subscribe(ReconTopics.START)
            async for message in messages:
                trace_id = str(uuid.uuid4())
                domain = message.payload.decode()

                LOGGER.debug(
                    'Starting pipeline',
                    extra=extra(trace_id, domain=domain))

                payload = json.dumps({
                    'trace_id': trace_id,
                    'domain': domain,
                })

                await client.publish(ReconTopics.SUBDOMAIN_ENUMERATION, payload)
                await client.publish(ReconTopics.DNS_VULN_SCAN, payload)
                await client.publish('webapp/start', payload)


async def main():
    configure_log()

    LOGGER.debug('MQTT_HOST: %s', MQTT_HOST)
    LOGGER.debug('MQTT_PORT: %d', MQTT_PORT)

    cancellation_event = asyncio.Event()

    def cancellation_handler(signum, frame):
        LOGGER.info('Handling signum %d', signum)
        cancellation_event.set()

    signal.signal(signal.SIGINT, cancellation_handler)
    signal.signal(signal.SIGTERM, cancellation_handler)

    tasks = [
        asyncio.create_task(subdomain_enumeration.run_main_loop()),
        asyncio.create_task(subdomains_info_gathering.run_main_loop()),
        asyncio.create_task(dns_vuln_scan.run_main_loop()),
        asyncio.create_task(watch_start_messages()),
    ]

    await cancellation_event.wait()

    LOGGER.debug('Cancelling tasks')

    for task in tasks:
        task.cancel()

    LOGGER.debug('Waiting for tasks to finish')

    for task in tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass

    LOGGER.debug('Bye')

if __name__ == '__main__':
    asyncio.run(main())
