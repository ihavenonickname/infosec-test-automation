import asyncio

import asyncio_mqtt as aiomqtt

from helper import MQTT_HOST, MQTT_PORT, run_program, check_installed, ReconTopics
from log import LOGGER


async def enumerate_subdomains(domain: str) -> list[str]:
    LOGGER.debug('Investigating domain %s', domain)

    async with asyncio.TaskGroup() as tg:
        amass_task = tg.create_task(
            run_program(
                'amass', 'enum', '-passive', '-norecursive', '-silent', '-d', domain
            )
        )
        subfinder_task = tg.create_task(
            run_program('subfinder', '-silent', '-d', domain)
        )
        findomain_task = tg.create_task(
            run_program('findomain', '-q', '-t', domain))

    LOGGER.debug('Done with %s', domain)

    subdomains = {
        *amass_task.result(),
        *subfinder_task.result(),
        *findomain_task.result(),
    }

    for subdomain in subdomains:
        LOGGER.info('Subdomain %s', subdomain)

    return subdomains


async def run_main_loop():
    LOGGER.debug('Checking if tools are installed')

    tools_ok = await check_installed('amass', 'subfinder', 'findomain')

    if not tools_ok:
        LOGGER.critical('Some tools are not installed')
        return

    async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
        async with client.messages() as messages:
            await client.subscribe(ReconTopics.SUBDOMAIN_ENUMERATION)
            async for message in messages:
                LOGGER.debug(
                    'Got message from topic %s with payload %s',
                    message.topic, message.payload)
                domain = message.payload.decode()
                subdomains = await enumerate_subdomains(domain)
                payload = '\n'.join(subdomains)
                await client.publish(ReconTopics.SUBDOMAINS_INFO_GATHERING, payload)
