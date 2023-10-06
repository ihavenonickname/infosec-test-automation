import asyncio
import json
import os
import signal
import uuid

import aiomqtt

from custom_logger import LOGGER, configure_log, extra
from steps import dns_scan
from steps import subdomain_enumeration
from steps import subdomains_info_gathering


MQTT_HOST = os.environ['MQTT_HOST']
MQTT_PORT = int(os.environ['MQTT_PORT'])


async def watch_messages():
    LOGGER.debug('Starting main run')

    handlers = [
        dns_scan.handler,
        subdomain_enumeration.handler,
        subdomains_info_gathering.handler,
    ]

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        async with client.messages() as messages:
            await client.subscribe('recon/#')
            async with asyncio.TaskGroup() as tg:
                async for message in messages:
                    payload = json.loads(message.payload)
                    if message.topic.matches('recon/start-pipeline'):
                        payload['trace_id'] = str(uuid.uuid4())
                        LOGGER.debug(
                            'Starting pipeline',
                            extra=extra(payload['trace_id'], domain=payload['domain']))
                        payload = json.dumps(payload)
                        await client.publish('recon/subdomain-enumeration', payload)
                        await client.publish('recon/dns-scan', payload)
                    else:
                        for handler in handlers:
                            if message.topic.matches(handler.topic):
                                tg.create_task(handler(payload, client))


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

    task = asyncio.create_task(watch_messages())

    LOGGER.debug('Idling in the foreground')

    await cancellation_event.wait()

    LOGGER.debug('Cancelling main task')

    task.cancel()

    LOGGER.debug('Waiting for main task to finish')

    try:
        await task
    except asyncio.CancelledError:
        pass

    LOGGER.debug('Bye')

if __name__ == '__main__':
    asyncio.run(main())
