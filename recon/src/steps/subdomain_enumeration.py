import asyncio
import json
from collections import defaultdict
from typing import cast

import aiomqtt

from helper import extract_trace_id, run_program
from custom_logger import LOGGER, extra
from messaging_abstractions import handle


@handle('recon/subdomain-enumeration')
async def handler(payload: dict[str, object], client: aiomqtt.Client) -> None:
    trace_id = extract_trace_id(payload)

    try:
        domain = cast(str, payload['domain'])
    except KeyError:
        LOGGER.exception('domain is required', extra=extra(trace_id))
        return

    LOGGER.debug('Enumerating subdomains',
                 extra=extra(trace_id, domain=domain))

    async with asyncio.TaskGroup() as tg:
        # amass_task = tg.create_task(run_program(
        #     'amass',
        #     'enum',
        #     '-passive',
        #     '-norecursive',
        #     '-silent',
        #     '-d',
        #     domain,
        #     trace_id=trace_id))

        subfinder_task = tg.create_task(run_program(
            'subfinder',
            '-silent',
            '-d',
            domain,
            trace_id=trace_id))

        findomain_task = tg.create_task(
            run_program('findomain', '-q', '-t', domain, trace_id=trace_id))

    subdomains = defaultdict(list)

    # for subdomain in amass_task.result():
    #     subdomains[subdomain].append('amass')

    for subdomain in subfinder_task.result():
        subdomains[subdomain].append('subfinder')

    for subdomain in findomain_task.result():
        subdomains[subdomain].append('findomain')

    for subdomain, found_by in subdomains.items():
        LOGGER.info(
            'Subdomain found',
            extra=extra(trace_id,
                        subdomain=subdomain,
                        found_by=','.join(found_by)))

    LOGGER.debug('Finished enumerating subdomains', extra=extra(trace_id))

    await client.publish('recon/webapp-scan', json.dumps({
        'trace_id': trace_id,
        'hostnames': subdomains,
    }))
