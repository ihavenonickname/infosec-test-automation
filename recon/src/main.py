import asyncio
import os
import signal

from custom_logger import LOGGER, configure_log
from messaging_abstractions import Fucker
from steps import dns_scan
from steps import subdomain_enumeration
from steps import webapp_scan


async def main():
    configure_log()

    mqtt_host = os.environ['MQTT_HOST']
    mqtt_port = int(os.environ['MQTT_PORT'])

    LOGGER.debug('MQTT_HOST: %s', mqtt_host)
    LOGGER.debug('MQTT_PORT: %d', mqtt_port)

    cancel_ev = asyncio.Event()

    def cancellation_handler(signum, frame):
        LOGGER.info('Handling signum %d', signum)
        cancel_ev.set()

    signal.signal(signal.SIGINT, cancellation_handler)
    signal.signal(signal.SIGTERM, cancellation_handler)

    fucker = Fucker(mqtt_host, mqtt_port, cancel_ev, [
        dns_scan.handler,
        subdomain_enumeration.handler,
        webapp_scan.handler,
    ])

    task = asyncio.create_task(fucker.loop_forever())

    LOGGER.debug('Idling in the foreground')

    await cancel_ev.wait()

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
