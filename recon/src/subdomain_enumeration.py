import asyncio
import json
from collections import defaultdict

import aiomqtt

from helper import MQTT_HOST, MQTT_PORT, run_program, check_installed, ReconTopics
from log import LOGGER, extra


async def enumerate_subdomains(domain: str, trace_id: str) -> list[str]:
    LOGGER.debug('Enumerating subdomains',
                 extra=extra(trace_id, domain=domain))

    async with asyncio.TaskGroup() as tg:
        amass_task = tg.create_task(run_program(
            'amass',
            'enum',
            '-passive',
            '-norecursive',
            '-silent',
            '-d',
            domain,
            trace_id=trace_id))

        subfinder_task = tg.create_task(run_program(
            'subfinder',
            '-silent',
            '-d',
            domain,
            trace_id=trace_id))

        findomain_task = tg.create_task(
            run_program('findomain', '-q', '-t', domain, trace_id=trace_id))

    subdomains = defaultdict(list)

    for subdomain in amass_task.result():
        subdomains[subdomain].append('amass')

    for subdomain in subfinder_task.result():
        subdomains[subdomain].append('subfinder')

    for subdomain in findomain_task.result():
        subdomains[subdomain].append('findomain')

    for subdomain, found_by in subdomains.items():
        found_by = ' '.join(found_by)
        LOGGER.info(
            'Subdomain found',
            extra=extra(trace_id, subdomain=subdomain, found_by=found_by))

    LOGGER.debug('Finished enumerating subdomains', extra=extra(trace_id))

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
                payload = json.loads(message.payload)
                trace_id = payload['trace_id']
                domain = payload['domain']

                subdomains = await enumerate_subdomains(domain, trace_id)

                payload = json.dumps({
                    'trace_id': trace_id,
                    'subdomains': subdomains,
                })

                await client.publish(ReconTopics.SUBDOMAINS_INFO_GATHERING, payload)
